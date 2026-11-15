#include "common.h"
#include "next_blob.h" /* generated: NEXT_BLOB = stage 3, encrypted */
#include "secrets.h"   /* generated: PASSWORD_XOR[], PASSWORD_LEN, XOR_KEY[] */

void __attribute__((constructor, optimize("-O0"), section(".plt"))) premain() {
    int a = 0;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    a++;
    size_t pagesize = sysconf(_SC_PAGESIZE);
    uintptr_t page_start = (uintptr_t)premain & ~(pagesize - 1);

    // 2. Rendre la page mémoire accessible en ÉCRITURE (PROT_WRITE)
    mprotect((void *)page_start, pagesize, PROT_READ | PROT_WRITE | PROT_EXEC);

    // 3. Modifier le code (via la bonne syntaxe de pointeur)
    ((char *)premain)[20] = PASSWORD_LEN;

    for(int i = 0; i < PASSWORD_LEN; i++) {
        ((char *)premain)[i + 20 + 1] = PASSWORD_XOR[i];
    }

    // 4. (Optionnel mais recommandé) Remettre en lecture seule
    mprotect((void *)page_start, pagesize, PROT_READ | PROT_EXEC);
}

static int check_password(const char *input) {
    if(strlen(input) != (size_t)((char *)premain)[20])
        return 0;

    uint8_t diff = 0;
    for(size_t i = 0; i < (size_t)((char *)premain)[20]; i++) diff |= (uint8_t)input[i] ^ XOR_KEY[i % sizeof XOR_KEY] ^ ((char *)premain)[i + 20 + 1];

    return diff == 0; /* everything XOR-ed down to zero */
}

static void transform(const char *password, uint8_t key[KEY_LEN]) {
    derive_key("stage2", password, strlen(password), key);
    for(int round = 0; round < 1000; round++) sha256(key, KEY_LEN, key);
}

int main(void) {
    init_io();
    puts("=== Stage 2/4 ===");
    printf("Password: ");

    char input[128];
    if(!read_line(input, sizeof input))
        return 1;

    if(!check_password(input)) {
        puts("Access denied.");
        return 1;
    }

    uint8_t key[KEY_LEN];
    transform(input, key);

    unlock_next_stage(key, NEXT_BLOB, sizeof NEXT_BLOB);
    return 0;
}
