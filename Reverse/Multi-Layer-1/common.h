/*
 * common.h - helpers shared by the four stages.
 *
 * Header-only on purpose: every stage is ONE .c file that includes this.
 *
 *   init_io()            unbuffered stdin/stdout (needed because we exec())
 *   read_line()          read one line from stdin with fgets
 *   derive_key()         the basic transform:  key = SHA-256(salt || data)
 *   aes256_gcm_open()    decrypt + authenticate a blob (wrong key => fails)
 *   unlock_next_stage()  decrypt the embedded blob and run it from memory
 *
 * Blob layout (produced by build.py):
 *
 *   [ IV : 12 bytes ][ ciphertext : N bytes ][ GCM tag : 16 bytes ]
 *
 * Build flag -DKEYGEN (used by build.py only, never shipped):
 *   instead of unlocking the next stage, print the key that the CORRECT
 *   answer produces. This is how the builder learns which key to encrypt with.
 */
#ifndef COMMON_H
#define COMMON_H

#ifndef _GNU_SOURCE
#define _GNU_SOURCE /* memfd_create, fexecve, explicit_bzero */
#endif

#include <openssl/evp.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>

#define KEY_LEN     32 /* AES-256 */
#define GCM_IV_LEN  12
#define GCM_TAG_LEN 16

extern char **environ;

/* ------------------------------------------------------------------ */
/* Input / output                                                      */
/* ------------------------------------------------------------------ */

/* Every stage is exec()'d inside the same process as the previous one:
 *  - stdout must not be buffered, or text printed just before exec() is lost
 *  - stdin must not be buffered, or the next stage would find it already
 *    emptied when the answers are piped in. */
static inline void init_io(void)
{
    setvbuf(stdin, NULL, _IONBF, 0);
    setvbuf(stdout, NULL, _IONBF, 0);
}

/* Read one line, strip the newline. Returns 0 on EOF. */
static inline int read_line(char *buf, size_t size)
{
    if (fgets(buf, (int)size, stdin) == NULL)
        return 0;
    buf[strcspn(buf, "\r\n")] = '\0';
    return 1;
}

static inline void hex_encode(const uint8_t *in, size_t len, char *out)
{
    for (size_t i = 0; i < len; i++)
        snprintf(out + 2 * i, 3, "%02x", in[i]);
}

/* ------------------------------------------------------------------ */
/* Crypto                                                              */
/* ------------------------------------------------------------------ */

static inline void sha256(const void *data, size_t len, uint8_t out[32])
{
    EVP_Digest(data, len, out, NULL, EVP_sha256(), NULL);
}

/* The "standard" transform: key = SHA-256(salt || data). */
static inline void derive_key(const char *salt, const void *data, size_t len,
                              uint8_t key[KEY_LEN])
{
    EVP_MD_CTX *ctx = EVP_MD_CTX_new();
    EVP_DigestInit_ex(ctx, EVP_sha256(), NULL);
    EVP_DigestUpdate(ctx, salt, strlen(salt));
    EVP_DigestUpdate(ctx, data, len);
    EVP_DigestFinal_ex(ctx, key, NULL);
    EVP_MD_CTX_free(ctx);
}

/* AES-256-GCM decrypt. Returns 1 and a malloc'ed buffer (NUL-terminated for
 * convenience) if the key is right, 0 if the authentication tag does not match. */
static inline int aes256_gcm_open(const uint8_t key[KEY_LEN],
                                  const uint8_t *blob, size_t blob_len,
                                  uint8_t **plain_out, size_t *plain_len_out)
{
    if (blob_len < GCM_IV_LEN + GCM_TAG_LEN)
        return 0;

    const uint8_t *iv     = blob;
    const uint8_t *ct     = blob + GCM_IV_LEN;
    size_t         ct_len = blob_len - GCM_IV_LEN - GCM_TAG_LEN;
    const uint8_t *tag    = ct + ct_len;

    uint8_t        *plain = malloc(ct_len + 1);
    EVP_CIPHER_CTX *ctx   = EVP_CIPHER_CTX_new();
    int len = 0, final_len = 0;

    int ok = plain && ctx
        && EVP_DecryptInit_ex(ctx, EVP_aes_256_gcm(), NULL, NULL, NULL)
        && EVP_CIPHER_CTX_ctrl(ctx, EVP_CTRL_GCM_SET_IVLEN, GCM_IV_LEN, NULL)
        && EVP_DecryptInit_ex(ctx, NULL, NULL, key, iv)
        && EVP_DecryptUpdate(ctx, plain, &len, ct, (int)ct_len)
        && EVP_CIPHER_CTX_ctrl(ctx, EVP_CTRL_GCM_SET_TAG, GCM_TAG_LEN, (void *)tag)
        && EVP_DecryptFinal_ex(ctx, plain + len, &final_len); /* checks the tag */

    EVP_CIPHER_CTX_free(ctx);
    if (!ok) {
        free(plain);
        return 0;
    }
    plain[ct_len] = '\0';
    *plain_out     = plain;
    *plain_len_out = ct_len;
    return 1;
}

/* ------------------------------------------------------------------ */
/* Chaining                                                            */
/* ------------------------------------------------------------------ */

/* Run an ELF that only exists in memory. Never returns on success.
 * The key is handed over as argv[1] (stage 3 uses it to seed its problem). */
static inline void exec_from_memory(const uint8_t *elf, size_t len,
                                    const uint8_t key[KEY_LEN])
{
    int fd = memfd_create("stage", 0);
    if (fd < 0) {
        perror("memfd_create");
        exit(1);
    }
    for (size_t done = 0; done < len;) {
        ssize_t n = write(fd, elf + done, len - done);
        if (n <= 0) {
            perror("write");
            exit(1);
        }
        done += (size_t)n;
    }

    char key_hex[2 * KEY_LEN + 1];
    hex_encode(key, KEY_LEN, key_hex);
    char *argv[] = { "stage", key_hex, NULL };
    fexecve(fd, argv, environ);
    perror("fexecve");
    exit(1);
}

#ifdef KEYGEN
/* Builder-only: report the key the correct answer leads to, then stop. */
static inline void keygen_print_and_exit(const uint8_t key[KEY_LEN])
{
    char key_hex[2 * KEY_LEN + 1];
    hex_encode(key, KEY_LEN, key_hex);
    puts(key_hex);
    exit(0);
}
#endif

/* Last step of stages 1-3: try to open the embedded next stage with `key`. */
static inline void unlock_next_stage(const uint8_t key[KEY_LEN],
                                     const uint8_t *blob, size_t blob_len)
{
#ifdef KEYGEN
    (void)blob;
    (void)blob_len;
    keygen_print_and_exit(key);
#else
    uint8_t *elf;
    size_t   elf_len;

    if (!aes256_gcm_open(key, blob, blob_len, &elf, &elf_len)) {
        puts("The next stage stays encrypted. Your solution isn't optimal.");
        exit(1);
    }
    puts("Decryption OK, launching the next stage...\n");
    exec_from_memory(elf, elf_len, key);
#endif
}

#endif /* COMMON_H */
