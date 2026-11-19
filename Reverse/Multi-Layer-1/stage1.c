#include "common.h"
#include "next_blob.h" /* generated: NEXT_BLOB = stage 2, AES-256-GCM encrypted */
#include "secrets.h"   /* generated: HIDDEN_PASSPHRASE */

static const char *const LEFTOVERS[] __attribute__((used)) = {
    "hunter2", "correct-horse-battery-staple", "admin:admin", HIDDEN_PASSPHRASE, "letmein-2024", "not-the-passphrase",
};

int main(void) {
    init_io();
    puts("=== Stage 1/4 ===");
    puts("The vault is locked. Surely someone left the passphrase lying around...");
    printf("Passphrase: ");

    char input[128];
    if(!read_line(input, sizeof input))
        return 1;

    /* Transform: key = SHA-256("stage1" || input) */
    uint8_t key[KEY_LEN];
    derive_key("stage1", input, strlen(input), key);

    unlock_next_stage(key, NEXT_BLOB, sizeof NEXT_BLOB);
    return 0;
}
