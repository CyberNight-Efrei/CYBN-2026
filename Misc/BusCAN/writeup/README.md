Les identifiants sur 29 bits et les messages spontanés EEC1 (`0xF004`, adresse source `0x00`), CCVS1 (`0xFEF1`) et ET1 (`0xFEEE`) permettent de reconnaître J1939. La consigne demande l'identification logicielle du calculateur moteur : c'est le PGN standard 65242 (`0xFEDA`), transmis sur demande.

On envoie le PGN Request 59904 (`0xEA00`) à l'adresse globale `0xFF`. Son contenu est le PGN demandé, sur trois octets en ordre faible d'abord :

```text
18EAFFFA#DAFE00
```

Ici `0xFA` est l'adresse source de l'outil de diagnostic. Le calculateur moteur (`0x00`) annonce une réponse multipaquet avec TP.CM BAM (`0x1CECFF00`), puis envoie les morceaux avec TP.DT (`0x1CEBFF00`). Le premier octet de chaque TP.DT est son numéro de séquence. Le premier octet du contenu reconstitué indique le nombre de champs d'identification ; le texte ASCII se termine par `*`.

Le solveur suivant envoie la requête et affiche l'identification, qui contient le flag :

```powershell
python solve.py HOST PORT
```
