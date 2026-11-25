#include <stdint.h>
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "esp_log.h"
#include "esp_bt.h"
#include "esp_bt_main.h"
#include "esp_gap_bt_api.h"
#include "esp_spp_api.h"
#include "nvs.h"
#include "nvs_flash.h"

#include "rolling_codes.h"
#include "crypto.h"

#define FLAG "CYBN{la_stack_bluetooth_etait_galere_a_implementer_mdr}"
#define SEED 0x81b5d610

#define SPP_TAG "ROLLING_CODES"
#define SPP_SERVER_NAME "ROLLING_CODES_SERVER"

static char local_device_name[32] = {0};
static const esp_spp_mode_t esp_spp_mode = ESP_SPP_MODE_CB;
static const bool esp_spp_enable_l2cap_ertm = true;

static const esp_spp_sec_t sec_mask = ESP_SPP_SEC_AUTHENTICATE;
static const esp_spp_role_t role_slave = ESP_SPP_ROLE_SLAVE;

static const char status_message[] = "Battery: 76%\nPosition: LOCKED\nAuthor: 0x7fff00";
static const char lock_message[] = "ok";
static const char unlock_message[] = FLAG;
static const char unknown_command_message[] = "Unknown command.\nAvailable: STATUS, LOCK, UNLOCK";
static const char wrong_length_message[] = "Err: wrong length";
static const char wrong_code_message[] = "Err: wrong code";
static const char correct_code_message[] = "ok";

static uint32_t previous_code;

static enum conn_status_t {
    NOT_CONNECTED,
    NOT_AUTHENTICATED,
    AUTHENTICATED,
    TO_DISCONNECT
} conn_status = NOT_CONNECTED;

static uint32_t conn_handle;
static nvs_handle_t nvs_page_handle;

static void esp_spp_cb(esp_spp_cb_event_t event, esp_spp_cb_param_t *param)
{
    switch (event)
    {
    case ESP_SPP_INIT_EVT:
        if (param->init.status == ESP_SPP_SUCCESS)
        {
            esp_spp_start_srv(sec_mask, role_slave, 1, SPP_SERVER_NAME);
        }
        else
        {
            ESP_LOGE(SPP_TAG, "ESP_SPP_INIT_EVT status:%d", param->init.status);
        }
        break;
    case ESP_SPP_START_EVT:
        if (param->start.status == ESP_SPP_SUCCESS)
        {
            esp_bt_gap_set_device_name(local_device_name);
            esp_bt_gap_set_scan_mode(ESP_BT_CONNECTABLE, ESP_BT_GENERAL_DISCOVERABLE);
        }
        else
        {
            ESP_LOGE(SPP_TAG, "ESP_SPP_START_EVT status:%d", param->start.status);
        }
        break;
    case ESP_SPP_SRV_OPEN_EVT:
        if (conn_status != NOT_CONNECTED)
        {
            esp_spp_disconnect(param->open.handle);
            ESP_LOGI(SPP_TAG, "Connection rejected: already in use");
        }
        else
        {
            conn_status = NOT_AUTHENTICATED;
            conn_handle = param->open.handle;
            uint32_t p = previous_code;
            previous_code = next_code();

            ESP_ERROR_CHECK(nvs_set_u32(nvs_page_handle, "seed", p));
            ESP_ERROR_CHECK(nvs_commit(nvs_page_handle));

            esp_spp_write(param->open.handle, sizeof(p), (uint8_t *)(&p));
            ESP_LOGI(SPP_TAG, "Handle %d connected", conn_handle);
            ESP_LOGI(SPP_TAG, "Initializing auth. p: %x", p);
        }
        break;
    case ESP_SPP_CLOSE_EVT:
        if (param->close.handle == conn_handle && conn_status != NOT_CONNECTED)
        {
            conn_status = NOT_CONNECTED;
        }
        ESP_LOGI(SPP_TAG, "Handle %d disconnected", param->close.handle);
        break;
    case ESP_SPP_DATA_IND_EVT:
        if (param->data_ind.handle != conn_handle)
        {
            esp_spp_disconnect(param->data_ind.handle);
            break;
        }

        switch (conn_status)
        {
        case NOT_CONNECTED:
            /* wtf */
            esp_spp_disconnect(param->data_ind.handle);
            break;
        case NOT_AUTHENTICATED:
            if (param->data_ind.len != sizeof(previous_code))
            {
                conn_status = TO_DISCONNECT;
                esp_spp_write(param->data_ind.handle, strlen(wrong_length_message), (uint8_t *)wrong_length_message);
                ESP_LOGI(SPP_TAG, "Wrong code length: %d instead of %d", param->data_ind.len, sizeof(previous_code));
                break;
            }

            uint32_t x;
            memcpy(&x, param->data_ind.data, sizeof(x));

            if (x != previous_code)
            {
                conn_status = TO_DISCONNECT;
                esp_spp_write(param->data_ind.handle, strlen(wrong_code_message), (uint8_t *)wrong_code_message);
                ESP_LOGI(SPP_TAG, "Wrong code : %x instead of %x", x, previous_code);
                break;
            }

            conn_status = AUTHENTICATED;
            esp_spp_write(param->data_ind.handle, strlen(correct_code_message), (uint8_t *)correct_code_message);
            ESP_LOGI(SPP_TAG, "Auth!");
            break;
        case AUTHENTICATED:
            if (strncmp((char *)param->data_ind.data, "LOCK", strlen("LOCK")) == 0)
            {
                esp_spp_write(param->data_ind.handle, strlen(lock_message), (uint8_t *)lock_message);
                ESP_LOGI(SPP_TAG, "Lock");
            }
            else if (strncmp((char *)param->data_ind.data, "UNLOCK", strlen("UNLOCK")) == 0)
            {
                esp_spp_write(param->data_ind.handle, strlen(unlock_message), (uint8_t *)unlock_message);
                ESP_LOGI(SPP_TAG, "Unlock");
            }
            else if (strncmp((char *)param->data_ind.data, "STATUS", strlen("STATUS")) == 0)
            {
                esp_spp_write(param->data_ind.handle, strlen(status_message), (uint8_t *)status_message);
                ESP_LOGI(SPP_TAG, "Status");
            }
            else
            {
                esp_spp_write(param->data_ind.handle, strlen(unknown_command_message), (uint8_t *)unknown_command_message);
                ESP_LOGI(SPP_TAG, "Unkown command");
            }
            break;
        default:
            break;
        }
        break;
    case ESP_SPP_WRITE_EVT:
        if (param->write.handle != conn_handle || conn_status == TO_DISCONNECT)
        {
            esp_spp_disconnect(param->write.handle);
        }
        break;
    default:
        break;
    }
}


esp_err_t rolling_codes_init(char name[], uint8_t name_length)
{
    memcpy(local_device_name, name, name_length);

    ESP_ERROR_CHECK(nvs_open("settings", NVS_READWRITE, &nvs_page_handle));

    uint32_t seed;

    esp_err_t err = nvs_get_u32(nvs_page_handle, "seed", &seed);

    if (err == ESP_ERR_NVS_NOT_FOUND) {
        seed = SEED;
        ESP_ERROR_CHECK(nvs_set_u32(nvs_page_handle, "seed", seed));
        ESP_ERROR_CHECK(nvs_commit(nvs_page_handle));
    } else {
        ESP_ERROR_CHECK(err);
    }

    code_init(seed);
    previous_code = next_code();

    esp_err_t ret;

    if ((ret = esp_spp_register_callback(esp_spp_cb)) != ESP_OK)
    {
        ESP_LOGE(SPP_TAG, "SPP register failed: %s",
                 esp_err_to_name(ret));
        return ret;
    }

    esp_spp_cfg_t bt_spp_cfg = {
        .mode = esp_spp_mode,
        .enable_l2cap_ertm = esp_spp_enable_l2cap_ertm,
        .tx_buffer_size = 0,
    };

    if ((ret = esp_spp_enhanced_init(&bt_spp_cfg)) != ESP_OK)
    {
        ESP_LOGE(SPP_TAG, "SPP init failed: %s",
                 esp_err_to_name(ret));
        return ret;
    }

    // Configuration du Legacy Pairing
    esp_bt_pin_type_t pin_type = ESP_BT_PIN_TYPE_FIXED;
    esp_bt_pin_code_t pin_code = {'5', '9', '3', '5'};

    esp_bt_gap_set_pin(pin_type, 4, pin_code);

    return ESP_OK;
}
