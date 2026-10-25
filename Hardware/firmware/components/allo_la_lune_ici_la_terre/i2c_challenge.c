
#include <stdint.h>
#include "driver/i2c_slave.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/queue.h"
#include "esp_err.h"

#define I2C_SDA_PIN    26
#define I2C_SCL_PIN    27
#define I2C_SLAVE_ADDR 0x42

static const uint8_t flag[] = "CYBN{c2hvcnR1cmwubHkvd2VsbFo=}";

static i2c_slave_dev_handle_t slave_handle;
static QueueHandle_t request_queue;

// Called whenever the I2C master requests data
static bool on_request(i2c_slave_dev_handle_t handle,
                       const i2c_slave_request_event_data_t *event,
                       void *arg)
{
    uint8_t request = 1;
    BaseType_t woken = pdFALSE;

    xQueueSendFromISR(request_queue, &request, &woken);
    return woken == pdTRUE;
}

static void i2c_challenge_task(void *arg)
{
    uint8_t request;

    while (1) {
        if (xQueueReceive(request_queue, &request, portMAX_DELAY)) {
            uint32_t written = 0;

            // Send the flag
            ESP_ERROR_CHECK(i2c_slave_write(
                slave_handle,
                flag,
                sizeof(flag) - 1,
                &written,
                1000
            ));
        }
    }
}

esp_err_t i2c_challenge_init(void)
{
    esp_err_t ret;

    request_queue = xQueueCreate(16, sizeof(uint8_t));
    
    if (!request_queue)
    {
        return ESP_ERR_NO_MEM;
    }

    i2c_slave_config_t config = {
        .i2c_port = 0,
        .clk_source = I2C_CLK_SRC_DEFAULT,
        .scl_io_num = I2C_SCL_PIN,
        .sda_io_num = I2C_SDA_PIN,
        .slave_addr = I2C_SLAVE_ADDR,
        .send_buf_depth = 128,
        .receive_buf_depth = 128,
    };

    ret = i2c_new_slave_device(&config, &slave_handle);
    if (ret != ESP_OK)
    {
        return ret;
    }

    i2c_slave_event_callbacks_t callbacks = {
        .on_request = on_request,
    };

    ret = i2c_slave_register_event_callbacks(
        slave_handle, &callbacks, NULL
    );
    if (ret != ESP_OK)
    {
        return ret;
    }

    // Start the I2C worker task
    BaseType_t result = xTaskCreate(
        i2c_challenge_task,
        "i2c_challenge",
        4096,
        NULL,
        5,
        NULL
    );

    return (result == pdPASS) ? ESP_OK : ESP_ERR_NO_MEM;
}
