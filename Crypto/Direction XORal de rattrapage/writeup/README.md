# Direction XORal de rattrapage - Writeup

Le script `locker.py` crée une seule clé aléatoire de huit octets, puis l'utilise en boucle sur
les trois fichiers. La clé n'est pas présente dans le code, mais `background.png.locked` donne
un texte clair connu : tous les PNG commencent par les huit octets suivants :

```text
89 50 4e 47 0d 0a 1a 0a
```

Pour un chiffrement XOR, `chiffré XOR clair = clé`. Ces huit octets suffisent donc à récupérer
la clé complète et à déchiffrer tous les fichiers :

```python
from pathlib import Path

signature = bytes.fromhex("89 50 4e 47 0d 0a 1a 0a")
png = Path("background.png.locked").read_bytes()
key = bytes(a ^ b for a, b in zip(png[:8], signature))

for name in ("background.png", "music.mp3", "message_prof.txt"):
    data = Path(name + ".locked").read_bytes()
    clear = bytes(byte ^ key[i % 8] for i, byte in enumerate(data))
    Path(name).write_bytes(clear)
```

En ouvrant `message_prof.txt`, on obtient le message du professeur et le code d'accès :

```text
CYBN{hug0_4_8_0ct3ts_m41s_0_sur_20}
```

Le MP3 distribué ne contient pas de tag ID3 et le message texte ne possède aucun en-tête fixe.
Des attaques par texte supposé restent possibles, mais nécessitent de deviner son contenu exact
et sont nettement moins directes que l'utilisation de la signature PNG.
