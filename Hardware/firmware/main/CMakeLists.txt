idf_component_register(SRCS "main.c"
                    REQUIRES bt_server_init rolling_codes claque_ton_sub nvs_flash allo_la_lune_ici_la_terre
                    INCLUDE_DIRS ".")
