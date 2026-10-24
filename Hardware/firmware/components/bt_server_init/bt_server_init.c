
#include "bt_server_init.h"

#include "esp_bt.h"
#include "esp_bt_main.h"
#include "esp_log.h"

#define BT_TAG "BLUETOOTH"

esp_err_t bluetooth_init(void)
{
    esp_err_t ret;

    esp_bt_controller_config_t bt_cfg =
        BT_CONTROLLER_INIT_CONFIG_DEFAULT();

    ret = esp_bt_controller_init(&bt_cfg);
    if (ret != ESP_OK) {
        ESP_LOGE(BT_TAG, "Controller init failed: %s",
                 esp_err_to_name(ret));
        return ret;
    }

    ret = esp_bt_controller_enable(ESP_BT_MODE_BTDM);
    if (ret != ESP_OK) {
        ESP_LOGE(BT_TAG, "Controller enable failed: %s",
                 esp_err_to_name(ret));
        esp_bt_controller_deinit();
        return ret;
    }

    esp_bluedroid_config_t bluedroid_cfg =
        BT_BLUEDROID_INIT_CONFIG_DEFAULT();

    bluedroid_cfg.ssp_en = false;

    ret = esp_bluedroid_init_with_cfg(&bluedroid_cfg);
    if (ret != ESP_OK) {
        ESP_LOGE(BT_TAG, "Bluedroid init failed: %s",
                 esp_err_to_name(ret));
        esp_bt_controller_disable();
        esp_bt_controller_deinit();
        return ret;
    }

    ret = esp_bluedroid_enable();
    if (ret != ESP_OK) {
        ESP_LOGE(BT_TAG, "Bluedroid enable failed: %s",
                 esp_err_to_name(ret));
        esp_bluedroid_deinit();
        esp_bt_controller_disable();
        esp_bt_controller_deinit();
        return ret;
    }

    ESP_LOGI(BT_TAG, "Bluetooth initialized (BTDM)");

    return ESP_OK;
}
