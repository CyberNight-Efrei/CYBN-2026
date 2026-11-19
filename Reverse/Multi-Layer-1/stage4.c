#include "common.h"
#include "next_blob.h" /* generated: NEXT_BLOB = the flag, encrypted */
#include <dirent.h>
#include <fcntl.h>

#define FINGERPRINT_LEN 256
#define HASH_LEN 32

/* Global, not local: see the file header above for why that matters.
 * Holds SHA-256(raw fingerprint) - 32 opaque bytes, never the MAC
 * addresses themselves in any printable form. */
static uint8_t g_fingerprint_hash[HASH_LEN];

/* Every non-loopback network interface's MAC address, concatenated in
 * directory order, into a LOCAL buffer - never stored anywhere static.
 * Several interfaces (wired + wifi, a VPN, a container bridge...) all
 * contribute, so the fingerprint is not just one value to reproduce by
 * chance - it is whatever /sys/class/net/ lists, that day, on that
 * machine.
 *
 * Deliberately open()/read()/close() instead of fopen()/fgets(): stdio
 * keeps its own internal buffer for a FILE*, a second copy of whatever it
 * read that fclose() does not clear. A raw read() puts the bytes only in
 * OUR buffer, which we explicitly wipe below - otherwise a MAC address
 * could still turn up in the core dump, in that leftover stdio buffer, at
 * whatever (unpredictable, heap-allocated) address it happened to get. */
static void read_fingerprint(char *out, size_t out_size) {
    out[0] = '\0';

    DIR *d = opendir("/sys/class/net");
    if(!d)
        return;

    struct dirent *entry;
    while((entry = readdir(d)) != NULL) {
        if(entry->d_name[0] == '.' || strcmp(entry->d_name, "lo") == 0)
            continue;

        char path[320];
        snprintf(path, sizeof path, "/sys/class/net/%s/address", entry->d_name);

        int fd = open(path, O_RDONLY);
        if(fd < 0)
            continue;

        char mac[64] = {0};
        ssize_t n = read(fd, mac, sizeof mac - 1);
        close(fd);
        if(n > 0) {
            mac[n] = '\0';
            strncat(out, mac, out_size - strlen(out) - 1);
        }
        explicit_bzero(mac, sizeof mac);
    }
    closedir(d);
}

/* Transform: key = SHA-256("stage4" || SHA-256(fingerprint)). The inner
 * hash is what ends up at a fixed, static address (g_fingerprint_hash);
 * the outer one is computed fresh every time, here and offline. */
static void vault_kdf(const uint8_t fingerprint_hash[HASH_LEN], uint8_t key[KEY_LEN]) { derive_key("stage4", fingerprint_hash, HASH_LEN, key); }

int main(void) {
    init_io();

    puts("FLAG 3 : CYBN{W4S_TR4NSP0RT_0PT1M1S5T10N_FUN}");

    puts("=== Stage 4/4 ===");
    puts("[vault] fingerprinting this host...");

    char fingerprint[FINGERPRINT_LEN];
    read_fingerprint(fingerprint, sizeof fingerprint);
    sha256(fingerprint, strlen(fingerprint), g_fingerprint_hash);
    explicit_bzero(fingerprint, sizeof fingerprint); /* raw MACs: gone */

    uint8_t key[KEY_LEN];
    vault_kdf(g_fingerprint_hash, key);

#ifdef KEYGEN
    keygen_print_and_exit(key);
#endif

    uint8_t *secret;
    size_t secret_len;
    if(!aes256_gcm_open(key, NEXT_BLOB, sizeof NEXT_BLOB, &secret, &secret_len)) {
        puts("[vault] unseal failed: this is not the machine that sealed it.");
        return 1;
    }

    /* This confirms the fingerprint really does produce the right key on
     * THIS machine (useful while you build the challenge) - but the
     * plaintext itself never gets a fixed address, and never survives
     * past this point: wiped (not just freed) before the program aborts,
     * so it is NOT in the core dump you hand to players. Only
     * g_fingerprint_hash is - that is the one thing they are meant to
     * recover from it and feed back through vault_kdf() themselves. */
    explicit_bzero(key, sizeof key);
    explicit_bzero(secret, secret_len);
    free(secret);

    puts("[vault] secret unsealed, then wiped. Nothing left to output.");
    puts("[vault] audit hook: aborting.");
    abort();
}
