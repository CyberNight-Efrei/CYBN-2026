#include <stdio.h>
#include <stdlib.h>

#include "esp_log.h"
#include "nvs_flash.h"

#include "bt_server_init.h"
#include "rolling_codes.h"
#include "claque_ton_sub.h"

void app_main() {
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND)
    {
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);

    ESP_ERROR_CHECK(bluetooth_init());
    
    ESP_ERROR_CHECK(rolling_codes_init());

    ESP_ERROR_CHECK(ble_server_init());
}
