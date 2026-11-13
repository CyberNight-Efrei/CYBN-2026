
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>

#include "esp_err.h"
#include "esp_log.h"
#include "esp_gap_ble_api.h"
#include "esp_gatts_api.h"
#include "esp_gatt_common_api.h"

#include "claque_ton_sub.h"

#define TAG "CLAQUE_TON_SUB"

#define BLE_APP_ID       0

static char ble_device_name[32] = {0};

static const uint8_t service_uuid[16] = {
    0x00, 0x00, 0x00, 0x00,
    0x00, 0x00,
    0x00, 0x80,
    0x00, 0x40,
    0x00, 0x00,
    0x00, 0x00, 0xFF, 0x7F
};

static const uint8_t write_uuid[16] = {
    0x00, 0x00, 0x00, 0x00,
    0x00, 0x00,
    0x00, 0x80,
    0x00, 0x40,
    0x00, 0x00,
    0x01, 0x00, 0xFF, 0x7F
};

static const uint8_t notify_uuid[16] = {
    0x00, 0x00, 0x00, 0x00,
    0x00, 0x00,
    0x00, 0x80,
    0x00, 0x40,
    0x00, 0x00,
    0x02, 0x00, 0xFF, 0x7F
};

#define CHUNK_SIZE 16

// JPEG embedded in firmware
extern const uint8_t image_start[] asm("_binary_flag_jpg_start");

extern const uint8_t image_end[] asm("_binary_flag_jpg_end");

char* image_err = "Index is not valid";

enum {
    IDX_SVC,

    IDX_NOTIFY_CHAR,
    IDX_NOTIFY_VAL,
    IDX_NOTIFY_CCCD,

    IDX_WRITE_CHAR,
    IDX_WRITE_VAL,

    IDX_NB
};

static uint16_t handles[IDX_NB];

static esp_gatt_if_t server_if = ESP_GATT_IF_NONE;
static uint16_t active_conn_id = 0;
static bool connected = false;
static bool notifications_enabled = false;
static bool service_started = false;
static bool adv_ready = false;
static bool adv_running = false;

// GATT UUIDs
static const uint16_t primary_service_uuid =
    ESP_GATT_UUID_PRI_SERVICE;

static const uint16_t character_declaration_uuid =
    ESP_GATT_UUID_CHAR_DECLARE;

static const uint16_t cccd_uuid =
    ESP_GATT_UUID_CHAR_CLIENT_CONFIG;

static const uint8_t notify_property =
    ESP_GATT_CHAR_PROP_BIT_NOTIFY;

static const uint8_t write_property =
    ESP_GATT_CHAR_PROP_BIT_WRITE;

static uint8_t notify_value[CHUNK_SIZE] = {0};
static uint8_t write_value[4] = {0};
static uint8_t cccd_value[2] = {0};

static const esp_gatts_attr_db_t gatt_db[IDX_NB] = {

    // Primary service
    [IDX_SVC] = {
        { ESP_GATT_AUTO_RSP },
        {
            ESP_UUID_LEN_16,
            (uint8_t *)&primary_service_uuid,
            ESP_GATT_PERM_READ,
            sizeof(service_uuid),
            sizeof(service_uuid),
            (uint8_t *)&service_uuid
        }
    },

    // NOTIFY characteristic declaration
    [IDX_NOTIFY_CHAR] = {
        { ESP_GATT_AUTO_RSP },
        {
            ESP_UUID_LEN_16,
            (uint8_t *)&character_declaration_uuid,
            ESP_GATT_PERM_READ,
            sizeof(notify_property),
            sizeof(notify_property),
            (uint8_t *)&notify_property
        }
    },

    // NOTIFY characteristic value
    [IDX_NOTIFY_VAL] = {
        { ESP_GATT_AUTO_RSP },
        {
            ESP_UUID_LEN_128,
            (uint8_t *)&notify_uuid,
            0,
            sizeof(notify_value),
            sizeof(notify_value),
            notify_value
        }
    },

    // Client Characteristic Configuration Descriptor
    [IDX_NOTIFY_CCCD] = {
        { ESP_GATT_RSP_BY_APP },
        {
            ESP_UUID_LEN_16,
            (uint8_t *)&cccd_uuid,
            ESP_GATT_PERM_READ | ESP_GATT_PERM_WRITE,
            sizeof(cccd_value),
            sizeof(cccd_value),
            cccd_value
        }
    },

    // WRITE characteristic declaration
    [IDX_WRITE_CHAR] = {
        { ESP_GATT_AUTO_RSP },
        {
            ESP_UUID_LEN_16,
            (uint8_t *)&character_declaration_uuid,
            ESP_GATT_PERM_READ,
            sizeof(write_property),
            sizeof(write_property),
            (uint8_t *)&write_property
        }
    },

    // WRITE characteristic value
    [IDX_WRITE_VAL] = {
        { ESP_GATT_RSP_BY_APP },
        {
            ESP_UUID_LEN_128,
            (uint8_t *)&write_uuid,
            ESP_GATT_PERM_WRITE,
            sizeof(write_value),
            sizeof(write_value),
            write_value
        }
    }
};

// BLE advertising
static esp_ble_adv_params_t adv_params = {
    .adv_int_min = 0x20,
    .adv_int_max = 0x40,
    .adv_type = ADV_TYPE_IND,
    .own_addr_type = BLE_ADDR_TYPE_PUBLIC,
    .channel_map = ADV_CHNL_ALL,
    .adv_filter_policy =
        ADV_FILTER_ALLOW_SCAN_ANY_CON_ANY,
};

static esp_ble_adv_data_t adv_data = {
    .set_scan_rsp = false,
    .include_name = true,
    .include_txpower = false,
    .flag = ESP_BLE_ADV_FLAG_GEN_DISC,
};

static size_t get_image_size(void)
{
    return (size_t)(image_end - image_start);
}

static uint32_t read_u32_le(const uint8_t *data)
{
    return
        ((uint32_t)data[0]) |
        ((uint32_t)data[1] << 8) |
        ((uint32_t)data[2] << 16) |
        ((uint32_t)data[3] << 24);
}

static void start_advertising(void)
{
    if (!adv_ready || !service_started ||
        connected || adv_running) {
        return;
    }

    esp_err_t err =
        esp_ble_gap_start_advertising(&adv_params);

    if (err == ESP_OK) {
        adv_running = true;
    } else {
        ESP_LOGE(TAG, "Advertising failed: %s",
                 esp_err_to_name(err));
    }
}

static void send_image_chunk(
    esp_gatt_if_t gatts_if,
    uint16_t conn_id,
    uint32_t index)
{
    if (!connected ||
        !notifications_enabled ||
        conn_id != active_conn_id) {
        ESP_LOGW(TAG, "Notifications unavailable");
        return;
    }

    size_t file_size = get_image_size();

    size_t total_chunks =
        file_size / CHUNK_SIZE +
        (file_size % CHUNK_SIZE != 0);

    if ((size_t)index >= total_chunks) {
            esp_err_t err = esp_ble_gatts_send_indicate(
            gatts_if,
            conn_id,
            handles[IDX_NOTIFY_VAL],
            strlen(image_err),
            (uint8_t *)image_err,
            false
        );

        ESP_LOGI(TAG, "Reading chunk outside of size, sending error");

        if (err != ESP_OK) {
            ESP_LOGE(TAG, "Notify failed: %s",
                    esp_err_to_name(err));
        }
        return;
    }

    size_t offset = (size_t)index * CHUNK_SIZE;
    size_t remaining = file_size - offset;

    size_t payload_len =
        remaining < CHUNK_SIZE
            ? remaining
            : CHUNK_SIZE;

    uint8_t packet[CHUNK_SIZE] = {0};

    memcpy(
        packet,
        image_start + offset,
        payload_len
    );

    esp_err_t err = esp_ble_gatts_send_indicate(
        gatts_if,
        conn_id,
        handles[IDX_NOTIFY_VAL],
        CHUNK_SIZE,
        packet,
        false
    );

    if (err != ESP_OK) {
        ESP_LOGE(TAG, "Notify failed: %s",
                 esp_err_to_name(err));
        return;
    }

    ESP_LOGI(
        TAG,
        "Chunk %lu: %u real bytes, %u padding bytes",
        (unsigned long)index,
        (unsigned)payload_len,
        (unsigned)(CHUNK_SIZE - payload_len)
    );
}


static void gap_event_handler(
    esp_gap_ble_cb_event_t event,
    esp_ble_gap_cb_param_t *param)
{
    switch (event) {

    case ESP_GAP_BLE_ADV_DATA_SET_COMPLETE_EVT:
        adv_ready = true;
        start_advertising();
        break;

    case ESP_GAP_BLE_ADV_START_COMPLETE_EVT:
        if (param->adv_start_cmpl.status ==
            ESP_BT_STATUS_SUCCESS) {
            ESP_LOGI(TAG, "BLE advertising started");
        } else {
            adv_running = false;
            ESP_LOGE(TAG, "Advertising start failed");
        }
        break;

    case ESP_GAP_BLE_ADV_STOP_COMPLETE_EVT:
        adv_running = false;
        break;

    default:
        break;
    }
}

static void handle_write(
    esp_gatt_if_t gatts_if,
    esp_ble_gatts_cb_param_t *param)
{
    uint16_t handle = param->write.handle;
    uint16_t conn_id = param->write.conn_id;

    esp_gatt_status_t status = ESP_GATT_OK;
    uint32_t requested_index = 0;

    if (param->write.is_prep) {
        status = ESP_GATT_REQ_NOT_SUPPORTED;
    }
    else if (!connected ||
             conn_id != active_conn_id) {
        status = ESP_GATT_ERROR;
    }
    else if (handle == handles[IDX_NOTIFY_CCCD]) {

        if (param->write.len != 2) {
            status = ESP_GATT_INVALID_ATTR_LEN;
        } else {
            uint16_t value =
                (uint16_t)param->write.value[0] |
                ((uint16_t)param->write.value[1] << 8);

            if (value == 0x0001) {
                notifications_enabled = true;
                ESP_LOGI(TAG, "Notifications enabled");
            }
            else if (value == 0x0000) {
                notifications_enabled = false;
                ESP_LOGI(TAG, "Notifications disabled");
            }
            else {
                status = ESP_GATT_ERROR;
            }

            if (status == ESP_GATT_OK) {
                memcpy(
                    cccd_value,
                    param->write.value,
                    2
                );
            }
        }
    }
    else if (handle == handles[IDX_WRITE_VAL]) {

        if (param->write.len != 4) {
            status = ESP_GATT_INVALID_ATTR_LEN;
        }
        else if (!notifications_enabled) {
            status = ESP_GATT_ERROR;
        }
        else {
            requested_index =
                read_u32_le(param->write.value);
        }
    }
    else {
        status = ESP_GATT_WRITE_NOT_PERMIT;
    }

    if (param->write.need_rsp) {
        esp_ble_gatts_send_response(
            gatts_if,
            conn_id,
            param->write.trans_id,
            status,
            NULL
        );
    }

    if (status == ESP_GATT_OK) {
        send_image_chunk(
            gatts_if,
            conn_id,
            requested_index
        );
    }
}

static void gatts_event_handler(
    esp_gatts_cb_event_t event,
    esp_gatt_if_t gatts_if,
    esp_ble_gatts_cb_param_t *param)
{
    switch (event) {

    case ESP_GATTS_REG_EVT: {

        if (param->reg.status != ESP_GATT_OK) {
            ESP_LOGE(TAG, "GATT registration failed");
            break;
        }

        server_if = gatts_if;

        ESP_ERROR_CHECK(
            esp_ble_gap_set_device_name(ble_device_name)
        );

        ESP_ERROR_CHECK(
            esp_ble_gap_config_adv_data(&adv_data)
        );

        ESP_ERROR_CHECK(
            esp_ble_gatts_create_attr_tab(
                gatt_db,
                gatts_if,
                IDX_NB,
                0
            )
        );

        break;
    }

    case ESP_GATTS_CREAT_ATTR_TAB_EVT: {

        if (param->add_attr_tab.status != ESP_GATT_OK) {
            ESP_LOGE(TAG, "Attribute table failed");
            break;
        }

        if (param->add_attr_tab.num_handle != IDX_NB) {
            ESP_LOGE(TAG, "Invalid attribute count");
            break;
        }

        memcpy(
            handles,
            param->add_attr_tab.handles,
            sizeof(handles)
        );

        ESP_ERROR_CHECK(
            esp_ble_gatts_start_service(handles[IDX_SVC])
        );

        break;
    }

    case ESP_GATTS_START_EVT:
        if (param->start.status == ESP_GATT_OK) {
            service_started = true;
            ESP_LOGI(TAG, "BLE service started");
            ESP_LOGI(TAG, "JPEG size: %u bytes",
                     (unsigned)get_image_size());
            start_advertising();
        }
        break;

    case ESP_GATTS_CONNECT_EVT:
        if (connected) {
            esp_ble_gatts_close(
                gatts_if,
                param->connect.conn_id
            );
            break;
        }

        connected = true;
        adv_running = false;
        notifications_enabled = false;
        active_conn_id = param->connect.conn_id;

        cccd_value[0] = 0;
        cccd_value[1] = 0;

        ESP_LOGI(TAG, "BLE client connected");
        break;

    case ESP_GATTS_DISCONNECT_EVT:
        connected = false;
        notifications_enabled = false;
        adv_running = false;

        cccd_value[0] = 0;
        cccd_value[1] = 0;

        ESP_LOGI(TAG, "BLE client disconnected");
        start_advertising();
        break;

    case ESP_GATTS_WRITE_EVT:
        handle_write(gatts_if, param);
        break;

    case ESP_GATTS_READ_EVT:
        if (param->read.handle ==
            handles[IDX_NOTIFY_CCCD]) {

            esp_gatt_rsp_t rsp = {0};
            rsp.attr_value.handle =
                handles[IDX_NOTIFY_CCCD];
            rsp.attr_value.len = 2;
            memcpy(rsp.attr_value.value, cccd_value, 2);

            esp_ble_gatts_send_response(
                gatts_if,
                param->read.conn_id,
                param->read.trans_id,
                ESP_GATT_OK,
                &rsp
            );
        }
        break;

    case ESP_GATTS_EXEC_WRITE_EVT:
        esp_ble_gatts_send_response(
            gatts_if,
            param->exec_write.conn_id,
            param->exec_write.trans_id,
            ESP_GATT_REQ_NOT_SUPPORTED,
            NULL
        );
        break;

    case ESP_GATTS_MTU_EVT:
        ESP_LOGI(TAG, "Negotiated MTU: %u",
                 param->mtu.mtu);
        break;

    case ESP_GATTS_CONGEST_EVT:
        ESP_LOGW(TAG, "Congestion: %d",
                 param->congest.congested);
        break;

    default:
        break;
    }
}

esp_err_t ble_server_init(char name[], uint8_t name_length)
{
    memcpy(ble_device_name, name, name_length);

    esp_err_t ret;

    ret = esp_ble_gap_register_callback(gap_event_handler);
    if (ret != ESP_OK)
    {
        return ret;
    }

    ret = esp_ble_gatts_register_callback(gatts_event_handler);
    if (ret != ESP_OK)
    {
        return ret;
    }

    ret = esp_ble_gatts_app_register(BLE_APP_ID);

    return ret;
}
