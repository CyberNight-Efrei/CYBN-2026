#include <stdint.h>

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/gpio.h"
#include "esp_err.h"

#define MORSE_GPIO GPIO_NUM_2

#define MORSE_DELAY 50

#define FLAG "C3_S01R_0N_M4NG3_DU_R1Z"

const char message[] = "SOS SOS LE FLAG EST " FLAG;
#define MESSAGE_SIZE sizeof(message) - 1

typedef struct
{
    char letter;
    char* morse_representation;
    uint8_t morse_representation_length;
} morse_letter_t;

static morse_letter_t morse_alphabet[] = {
    // Letters A-Z
    {'A', ".-",    2},
    {'B', "-...",  4},
    {'C', "-.-.",  4},
    {'D', "-..",   3},
    {'E', ".",     1},
    {'F', "..-.",  4},
    {'G', "--.",   3},
    {'H', "....",  4},
    {'I', "..",    2},
    {'J', ".---",  4},
    {'K', "-.-",   3},
    {'L', ".-..",  4},
    {'M', "--",    2},
    {'N', "-.",    2},
    {'O', "---",   3},
    {'P', ".--.",  4},
    {'Q', "--.-",  4},
    {'R', ".-.",   3},
    {'S', "...",   3},
    {'T', "-",     1},
    {'U', "..-",   3},
    {'V', "...-",  4},
    {'W', ".--",   3},
    {'X', "-..-",  4},
    {'Y', "-.--",  4},
    {'Z', "--..",  4},

    // Digits 0-9
    {'0', "-----", 5},
    {'1', ".----", 5},
    {'2', "..---", 5},
    {'3', "...--", 5},
    {'4', "....-", 5},
    {'5', ".....", 5},
    {'6', "-....", 5},
    {'7', "--...", 5},
    {'8', "---..", 5},
    {'9', "----.", 5},

    // Punctuation and symbols
    {'.', ".-.-.-", 6},   // Period
    {',', "--..--", 6},   // Comma
    {'?', "..--..", 6},   // Question mark
    {'\'', ".----.", 6},  // Apostrophe
    {'!', "-.-.--", 6},   // Exclamation mark
    {'/', "-..-.", 5},    // Slash
    {'(', "-.--.", 5},    // Left parenthesis
    {')', "-.--.-", 6},   // Right parenthesis
    {'&', ".-...", 5},    // Ampersand
    {':', "---...", 6},   // Colon
    {';', "-.-.-.", 6},   // Semicolon
    {'=', "-...-", 5},    // Equals sign
    {'+', ".-.-.", 5},    // Plus sign
    {'-', "-....-", 6},   // Hyphen
    {'_', "..--.-", 6},   // Underscore
    {'"', ".-..-.", 6},   // Quotation mark
    {'$', "...-..-", 7},  // Dollar sign
    {'@', ".--.-.", 6},   // At sign

    {' ', "", 0},
};

#define MORSE_ALPHABET_SIZE (sizeof(morse_alphabet) / sizeof(morse_alphabet[0]))


static void morse_task(void *_pvParameters)
{
    gpio_set_level(MORSE_GPIO, 0);
    
    while (1) {
        for (uint8_t msg_letter_counter = 0;
            msg_letter_counter < (MESSAGE_SIZE);
            msg_letter_counter++)
        {
            char c = message[msg_letter_counter];
            morse_letter_t *morse_letter = NULL;

            for (uint8_t i = 0; i < MORSE_ALPHABET_SIZE; i++)
            {
                if (morse_alphabet[i].letter == c)
                {
                    morse_letter = &(morse_alphabet[i]);
                    break;
                }
            }

            if (morse_letter == NULL)
            {
                continue;
            }

            for (uint8_t j = 0; j < morse_letter->morse_representation_length; j++)
            {
                char m = morse_letter->morse_representation[j];

                gpio_set_level(MORSE_GPIO, 1);

                if (m == '-')
                {
                    vTaskDelay(pdMS_TO_TICKS(MORSE_DELAY * 3));
                }
                else if (m == '.')
                {
                    vTaskDelay(pdMS_TO_TICKS(MORSE_DELAY * 1));
                }

                gpio_set_level(MORSE_GPIO, 0);
                
                vTaskDelay(pdMS_TO_TICKS(MORSE_DELAY * 1));
            }

            vTaskDelay(pdMS_TO_TICKS(MORSE_DELAY * 3));
        }

        vTaskDelay(pdMS_TO_TICKS(MORSE_DELAY * 9));
    }
}

esp_err_t morse_init(void)
{
    gpio_config_t io_conf = {
        .pin_bit_mask = (1ULL << MORSE_GPIO),
        .mode = GPIO_MODE_OUTPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE
    };

    esp_err_t ret = gpio_config(&io_conf);
    if (ret != ESP_OK)
    {
        return ret;
    }

    // Create a FreeRTOS task
    BaseType_t result = xTaskCreate(
        morse_task,
        "morse_task",
        2048,
        NULL,
        4,
        NULL
    );

    return (result == pdPASS) ? ESP_OK : ESP_ERR_NO_MEM;
}
