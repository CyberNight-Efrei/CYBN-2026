idf_component_register(SRCS "main.c"
                    REQUIRES bt_server_init rolling_codes claque_ton_sub nvs_flash
                    INCLUDE_DIRS ".")
