#include <Arduino.h>
#include <EEPROM.h>

#define SEED 0x1
#define KEY 0x0
#define ROUNDS 3431937419U
#define FLAG "CYBN{NOT_A_FLAG}"

#define BT_STATE_PIN 2
#define SEED_INIT_ADDRESS 0
#define SEED_ADDRESS 1

static enum conn_status_t {
    NOT_CONNECTED,
    NOT_AUTHENTICATED,
    WAITING_FOR_CODE,
    AUTHENTICATED,
    TO_DISCONNECT
} conn_status = NOT_CONNECTED;

uint32_t code = 0;

char incoming_code[4] = {0};
uint_fast8_t code_bytes_read = 0;

char incoming_command[8] = {0};
uint_fast8_t command_bytes_read = 0;

void setup()
{
    pinMode(BT_STATE_PIN, INPUT);

    Serial.begin(38400);

    Serial.print("AT+PIN5935");
    delay(1000);
    Serial.print("AT+NAMECYBERNIGHT-SMARTLOCK");
    Serial.flush();

    uint8_t seed_init;
    uint32_t seed;
    EEPROM.get(SEED_INIT_ADDRESS, seed_init);
    if (seed_init != 0)
    {
        EEPROM.get(SEED_ADDRESS, seed);
    }
    else
    {
        seed = SEED;
        EEPROM.put(SEED_INIT_ADDRESS, (uint8_t)1)
    }
    randomSeed(seed);

    // Simulate some codes
    for (uint32_t i = 0; i < ROUNDS; i++)
    {
        random();
    }

    code = (uint32_t)random() ^ KEY;
}

void loop()
{
    if (digitalRead(BT_STATE_PIN) == LOW)
    {
        conn_status = NOT_CONNECTED;
        code_bytes_read = 0;
        command_bytes_read = 0;
        memset(incoming_code, 0, sizeof(incoming_code));
        memset(incoming_command, 0, sizeof(incoming_command));
        return;
    }

    switch (conn_status)
    {
    case NOT_CONNECTED:
        conn_status = NOT_AUTHENTICATED;
        break;
    case NOT_AUTHENTICATED:
        Serial.write((uint8_t *)&code, sizeof(code));
        EEPROM.put(SEED_ADDRESS, code);
        code = random() ^ KEY;
        conn_status = WAITING_FOR_CODE;
        break;
    case WAITING_FOR_CODE:
        if (code_bytes_read < 4)
        {
            if (Serial.available() > 0)
            {
                incoming_code[code_bytes_read++] = Serial.read();
            }
        }
        else
        {
            uint32_t x;
            memcpy(&x, incoming_code, sizeof(x));
            if (x == code)
            {
                conn_status = AUTHENTICATED;
                Serial.print("ok");
                Serial.flush();
            }
            else
            {
                conn_status = TO_DISCONNECT;
            }
        }
        break;
    case AUTHENTICATED:
        // Read command
        while (Serial.available() > 0 && command_bytes_read < sizeof(incoming_command) - 1)
        {
            incoming_command[command_bytes_read++] = Serial.read();
            delay(1);
        }

        // Flush RX
        while (Serial.available())
            Serial.read();

        if (command_bytes_read > 0)
        {
            incoming_command[command_bytes_read] = '\0';

            if (strcmp(incoming_command, "LOCK") == 0)
            {
                Serial.print("ok");
            }
            else if (strcmp(incoming_command, "UNLOCK") == 0)
            {
                Serial.print(FLAG);
            }
            else if (strcmp(incoming_command, "STATUS") == 0)
            {
                Serial.print("Battery: 76%\nPosition: LOCKED\nAuthor: 0x7fff00");
            }
            else
            {
                Serial.print("Unknown command.\nAvailable: STATUS, LOCK, UNLOCK");
            }

            command_bytes_read = 0;
            memset(incoming_command, 0, sizeof(incoming_command));
        }
        break;
    case TO_DISCONNECT:
    default:
        break;
    }
}
