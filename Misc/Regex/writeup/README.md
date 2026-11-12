# Writeup — Sélection surnaturelle

**Catégorie :** Misc - Easy

L'objectif est de reconstruire le flag en décortiquant la regex, bloc par bloc.

## Décomposition

```text
\A                         → Début de chaîne
CYBN\{                     → Préfixe CYBN{
(?=.{40}\}\Z)              → 40 caractères entre les accolades
(?=[^}]*_p4ss3_)           → Contient _p4ss3_
(?=[^}]*_v4_)              → Contient _v4_
(?![^}]*[A-Z])             → Aucune majuscule dans le contenu

(?:(?=j)j)                 → j (assertion redondante)
(?P<digit>[0-9])           → 4 (imposé par _p4ss3_)
(?:1)                      → 1
_                          → _
(?:p(?P=digit))            → p4
(((((?P<letter>[a-z])))))  → Capture s (groupes imbriqués)
(?P=letter)                → s (référence à la capture)
(?:(?![48675291])\d)       → 3 (0 possible, mais exclu par _p4ss3_)

_l[3]_                     → _l3_
(?:c(?P=digit))            → c4
(?:s(?:t))                 → st
1                          → 1
(?:n)                      → n
g_                         → g_
(?:(?:m(?P=digit))){2}     → m4m4
n_                         → n_
(?:v(?P=digit))            → v4
_3                         → _3
(?:tr)                     → tr
3_f                        → 3_f
(?=13r3\})                 → Assertion redondante
1                          → 1
(?:3)                      → 3
r3                         → r3
\}                         → }
\Z                         → Fin de chaîne
```

## Flag

```text
CYBN{j41_p4ss3_l3_c4st1ng_m4m4n_v4_3tr3_f13r3}
```

Maman va être fière.