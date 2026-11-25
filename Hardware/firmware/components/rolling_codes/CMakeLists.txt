idf_component_register(SRCS "rolling_codes.c" "crypto.c"
                    PRIV_REQUIRES bt nvs_flash
                    INCLUDE_DIRS ".")
