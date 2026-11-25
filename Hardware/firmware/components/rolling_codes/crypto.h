#ifndef CRYPTO_H
#define CRYPTO_H

#include <stdint.h>

void code_init(uint32_t seed);

uint32_t next_code();

#endif