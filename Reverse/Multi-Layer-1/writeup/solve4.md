At the end of stage 3 we can put a breakpoint at fexecve(fd: v68, argv, envp: _environ); which lets us see the new binary is in fd 3 of this process
so we can do cp /proc/{PID}/fd/3 stage4

In this challenge, you're given a coredump, you can easily analyse it using ida. 
Also you can easily check that the binary is compiled with no-pie 
```
❯ checksec stage4
[*] '/home/sandor/Projects/CYBN-2026/CYBN-2026/Reverse/Multi-Layer-1/dist/solve/stage4'
    Arch:       amd64-64-little
    RELRO:      Partial RELRO
    Stack:      Canary found
    NX:         NX enabled
    PIE:        No PIE (0x400000)
```
As such the base of the program is always 0x400000 and the non dynamic addresses (mainly not in the heap or the stack or in a library) will always be at the same place.
When looking at the program, we see a lot of things reading files but we don't care about it.
```
  v10 = strlen(s: dest);
  v11 = EVP_sha256();
  EVP_Digest(a1: dest, a2: v10, a3: &byte_404120, a4: 0, a5: v11, a6: 0);
  explicit_bzero(a1: dest, a2: 256);
  v12 = EVP_MD_CTX_new();
  v13 = EVP_sha256();
  EVP_DigestInit_ex(a1: v12, a2: v13, a3: 0);
  EVP_DigestUpdate(a1: v12, a2: "stage4", a3: 6);
  EVP_DigestUpdate(a1: v12, a2: &byte_404120, a3: 32);
  EVP_DigestFinal_ex(a1: v12, a2: s, a3: 0);
  EVP_MD_CTX_free(a1: v12);
  v14 = malloc(size: 0x25u);
  v15 = EVP_CIPHER_CTX_new();
```
but we have this which is more interesting. Because first byte\_404120 is in the bss and as such at the same place in the coredump so we'll be able to easily retrieve its value.
We also easily understand that the program is doing a sha256 of it and then a second sha256 of "stage4" + &byte\_404120.
This hash is then used in the decryption process. 
```
   v18 = EVP_aes_256_gcm();
    if ( (unsigned int)EVP_DecryptInit_ex(a1: v16, a2: v18, a3: 0, a4: 0, a5: 0) != 0
      && (unsigned int)EVP_CIPHER_CTX_ctrl(a1: v16, a2: 9, a3: 12, a4: 0) != 0
      && (unsigned int)EVP_DecryptInit_ex(a1: v16, a2: 0, a3: 0, a4: s, a5: &unk_402160) != 0
      && (unsigned int)EVP_DecryptUpdate(a1: v16, a2: v14, a3: &v19, a4: &unk_40216C, a5: 36) != 0
      && (unsigned int)EVP_CIPHER_CTX_ctrl(a1: v16, a2: 17, a3: 16, a4: &unk_402190) != 0
      && (unsigned int)EVP_DecryptFinal_ex(a1: v16, a2: &v14[v19], a3: &v20) != 0 )
    {
      EVP_CIPHER_CTX_free(a1: v16);
      v14[36] = 0;
```
So what we need is to get the same value to enter the second sha256 function as the second sha256 function result is set to zero before the program crash so it's not in the coredump.
For this we can just go grab the value in the coredump start debugging and before the second sha256 function patch the memory with the right value.
then just put a breakpoint to read v14 which contains the flag :
```
      v14[36] = 0; //here
      explicit_bzero(a1: s, a2: 32);
      explicit_bzero(a1: v14, a2: 36);
      free(ptr: v14);
      puts(s: "[vault] secret unsealed, then wiped. Nothing left to output.");
      puts(s: "[vault] audit hook: aborting.");
      abort();
```

CYBN{3NF1N_F1N1_AV3C_C3TT3_H1ST01R3}
