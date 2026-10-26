#ifndef GET_FLAG_H
#define GET_FLAG_H

#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

int get_flag(const char *password, char *buf, size_t len);

#ifdef __cplusplus
}
#endif

#endif /* GET_FLAG_H */
