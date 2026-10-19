# Bloat less stack

*Qu'est ce qu'on peut faire dans cette boîte ?*

---

L'objectif du challenge et de forcer le challenger à utiliser l'assembly x86-64 pour lire le contenu du fichier de flag contenu lui meme dans un dossier. 

Pour se rendre compte qui fallait lancer de l'assembly x86-64 il fallait lire le code source de la page :
```html
<!--

frontend vibecodé sans une once de respect il faut le dire

ducoup en guise de compensation : https://fr.wikipedia.org/wiki/X64 

alors là vraiment de rien c'est cadeau \ (^_^) /

-->
```

Ou juste mettre n'importe quoi se qui déclenche une erreur sur les fichier "asm" :
```
p.asm:1: error: parser: instruction expected
p.asm:2: error: label or instruction expected at start of line
```

Il faut donc :

- lister le contenu du répertoire courant (code 1)

- lister le contenu du dossier découvert (code 1 legerement modifié)

- lire le fichier dans le dossier découvert (code 2)

Le write up suivant présente les programmes assembly limité au strict minimum pour récupérer le flag.

# Lister le contenu du répertoire courant

```assembly
section .bss
    buf: resb 4096 ; on définit un buffer qui va contenir le contenu à afficher

section .text
	global _start

_start:
    push 0x2e ; correspond au caractère "." pour lire le dossier courant
    mov rax, 2 ; rax contient le numéro du syscall 2 = sys_open
    mov rdi, rsp ; rsp pointe sur la première valeur dans la pile (".")
    xor rsi, rsi ; revient à faire mov rsi, 0 mais c'est plus opti pour le cpu de faire comme ça
    syscall ; sys_open(rdi = ".", rsi = 0 = O_RDONLY), le fd est renvoyé dans rax

    mov rdi, rax
    mov rax, 217
    mov rsi, buf
    mov rdx, 4096
    syscall ; getdents64(fd, buf, 4096)

    ; les données sont dans buf, rax contient le nombre d'octets écrits dedans
    ; rsi pointe toujours sur buf

    mov rdx, rax 
    mov rax, 1
    mov rdi, 1
    syscall ; write(rdi = 1 = stdout, rsi = buf, rdx = nombre d'octets à afficher)

    mov rax, 60
    xor rdi, rdi
    syscall
```
```
��.r��..	�� ticketbox
```

Une fois qu'on a retrouvé le dossier on va relancer presque le meme programme mais pour lister son contenu.

# Lister le contenu du dossier découvert

```assembly
; on déclare une section data qui va nous permettre de récupérer le chemin
; on en avait pas besoin avant puisque c'était juste un caractère donc on utilisait la pile
section .data
    dir: db "ticketbox", 0

section .bss
    buf: resb 4096

section .text
	global _start

_start:
    mov rax, 2
    mov rdi, dir
    xor rsi, rsi
    syscall

    mov rdi, rax
    mov rax, 217
    mov rsi, buf
    mov rdx, 4096
    syscall

    mov rdx, rax
    mov rax, 1
    mov rdi, 1
    syscall

    mov rax, 60
    xor rdi, rdi
    syscall
```
```
��.��..��8free_ticket_for_totoro_friend.txt
```

Maintenant qu'on a le nom du fichier on va pouvoir le lire.

# Lire le flag

```assembly
section .data
    path: db "ticketbox/free_ticket_for_totoro_friend.txt", 0

section .bss
    buf: resb 4096

section .text
	global _start

_start:
    ; open(path) le file descriptor (fd) va dans le registre rax
    mov rax, 2
    mov rdi, path
    xor rsi, rsi
    syscall

    ; Place le contenu du fichier correspondant au fd dans buf
    mov rdi, rax
    mov rax, 0
    mov rsi, buf
    mov rdx, 4096
    syscall ; read(fd, buf, 4096) le contenu va dans buf

    ; Afficher buf
    mov rdx, rax
    mov rax, 1
    mov rdi, 1
    syscall ; write(1, buf, rax)

    mov rax, 60
    xor rdi, rdi
    syscall
```
```
CYBN{LE_Chat-bus_ARRiVE_ATTenTION_AU_DEPaRT}
```