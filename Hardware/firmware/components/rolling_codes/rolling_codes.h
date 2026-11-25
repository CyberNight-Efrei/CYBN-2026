#ifndef ROLLING_CODES_H
#define ROLLING_CODES_H

#include "esp_err.h"

// Assumes the BT server has already been started (`bt_server_init`) and NVS flash already initialized
esp_err_t rolling_codes_init(char name[], uint8_t name_length);

#endif