# Write-up — « Les Trois Mousquetaires »

*Catégorie : stéganographie · Fichier fourni : `trois_mousquetaires.png` · 14 octobre 2026*

## Énoncé

> **Les Trois Mousquetaires** — Un pour tous, tous pour un... 

Un seul fichier est fourni : `trois_mousquetaires.png`, une photo de trois mousquetaires vus de dos (PNG RGB 8 bits, 1374 × 1145 px, 2 497 828 octets).

## 1. Reconnaissance

Un parcours des chunks PNG ne montre que `IHDR`, `IDAT` et `IEND` : aucune métadonnée, aucun octet après `IEND`, un flux zlib consommé en entier et des filtres de ligne ordinaires. Il n'y a rien à chercher en dehors des pixels.

## 2. Les LSB des trois canaux - "Un pour tous"

Premier réflexe : lire le LSB de l'image, c'est-à-dire R, G, B entrelacés, ligne par ligne. On n'obtient que du bruit. Normal : ici **chaque canal porte sa propre charge utile**. Il faut donc lire chaque plan **séparément** (ligne par ligne, bit de poids fort en premier) :

```python
import numpy as np
from PIL import Image

img = np.array(Image.open('trois_mousquetaires.png').convert('RGB'))
for ch, nom in enumerate('RGB'):
    bits = img[:, :, ch].reshape(-1) & 1                   # LSB du canal, ligne par ligne
    print(nom, np.packbits(bits[:72]).tobytes().hex(' '))  # juste les premiers octets
```

Les trois canaux commencent par **les mêmes 8 octets** :

```
R 00 01 4b 55 00 4c 01 74 03
G 00 01 4b 55 00 4c 01 74 03
B 00 01 4b 55 00 4c 01 74 03
```

C'est normal, c'est un en-tête « longueur + dimensions » :

- `00 01 4B 55` → longueur = `0x00014B55` = **84 821** octets ;
- `00 4C` → hauteur = **76** ;
- `01 74` → largeur = **372** ;

Vérification arithmétique : 76 × 372 × 3 = 84 816, et 84 816 + 5 octets (hauteur, largeur, canaux) = **84 821** ✓. Chaque canal contient donc une image RGB de 372 × 76 px, précédée de ses dimensions. L'en-tête est identique dans les trois canaux parce que les trois *shares* ont exactement la même taille.

Chaque canal occupe 4 + 84 821 = 84 825 octets, soit 678 600 bits : seuls les **678 600 premiers pixels** sont modifiés, le reste de l'image est vierge.

## 3. Étape 1 : XOR des trois canaux - "Tous pour un"

Les trois flux sont uniformes : ce sont des *shares* d'un partage de secret. Aucun n'est lisible seul. En XORant les trois flux octet par octet, on obtient après l'en-tête des petits octets qui évoluent doucement (`08 0c 10 08 0c 10 08 0c 10 …`). Ce ne sont pas des caractères mais des triplets RGB très sombres : lon obtient une **image**.

```python
import struct

def lsb_extract(arr):
    bits = arr.reshape(-1) & 1
    (n,) = struct.unpack('>I', np.packbits(bits[:32]).tobytes())
    return np.packbits(bits[32:32 + 8 * n]).tobytes()

shares = []
for ch in range(3):
    payload = lsb_extract(img[:, :, ch])
    h, w, c = struct.unpack('>HHB', payload[:5])
    shares.append(np.frombuffer(payload[5:], dtype=np.uint8).reshape(h, w, c))

secret = shares[0] ^ shares[1] ^ shares[2]
Image.fromarray(secret).save('secret.png')
```

L'image obtenue (372 × 76 px) affiche : **« One more thing... »**. Donc il nous reste une étape, on recommence la reconnaissance.

## 4. Étape 2 : LSB « classique » de l'image « One more thing... »

Ici, on prend le LSB de chaque valeur dans l'ordre de lecture (R₀, G₀, B₀, R₁, G₁, B₁, …). Les 32 premiers bits donnent la longueur du message, les suivants le message.

```python
flat = secret.reshape(-1) & 1
n = int.from_bytes(np.packbits(flat[:32]).tobytes(), 'big')
flag = np.packbits(flat[32:32 + 8 * n]).tobytes().decode()
print(flag)
```

## Flag

`CYBN{tr1PL3_l4yerS_st3G4n0}`
