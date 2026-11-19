#include <stdio.h>
#include <string.h>

#include "nvs_flash.h"
#include "esp_mac.h"

#include "bt_server_init.h"
#include "rolling_codes.h"
#include "claque_ton_sub.h"

#include "i2c_challenge.h"

#include "morse.h"

#include "esp_log.h"
#include "esp_err.h"
#include "nvs_flash.h"

static const char *TAG = "NVS";

void init_nvs(void)
{
    esp_err_t ret = nvs_flash_init();

    ESP_LOGI(TAG, "First NVS init: %s (0x%x)",
             esp_err_to_name(ret), (unsigned int)ret);

    if (ret == ESP_ERR_NVS_NO_FREE_PAGES ||
        ret == ESP_ERR_NVS_NEW_VERSION_FOUND)
    {
        ESP_LOGW(TAG, "Erasing NVS partition");

        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }

    ESP_LOGI(TAG, "Final NVS init: %s (0x%x)",
             esp_err_to_name(ret), (unsigned int)ret);

    ESP_ERROR_CHECK(ret);
}

void app_main() {
    char esp_name[32] = {0};
    uint8_t mac[6];
    esp_read_mac(mac, ESP_MAC_WIFI_STA);
    snprintf(esp_name, sizeof(esp_name), "%s%02X%02X", "CYBN-HW-", mac[4], mac[5]);

    init_nvs();

    ESP_ERROR_CHECK(bluetooth_init());
    ESP_ERROR_CHECK(rolling_codes_init(esp_name, strlen(esp_name)));
    ESP_ERROR_CHECK(ble_server_init(esp_name, strlen(esp_name)));
    ESP_ERROR_CHECK(i2c_challenge_init());
    ESP_ERROR_CHECK(morse_init());

    printf("\n\nLe nom de cet ESP32 est %s\n", esp_name);
    printf("Bon courage :)\n");
    fflush(stdout);
}
