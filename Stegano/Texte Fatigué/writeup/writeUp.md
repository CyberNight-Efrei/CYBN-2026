# Write-up — Texte Fatigué

Voici des infos qu'on vous a déjà dites pour cette soirée, mais je vous les réécris encore une fois, en plus je commence à fatigué, j'écris n'importe comment…

## Énoncé

On reçoit un fichier `rappel.txt` contenant un message d'apparence anodine :
Merｃｉ d＇ａvoir ｐｒiｓ le ｔｅmｐs ｄe ｔeｓter ｃe ｃhaｌｌｅngｅ． Ｐeｔｉt ｒaｐpel pｏｕr le ｒｅsｔｅ ｄe ｃｅtte mａｇniｆｉｑuｅ cｙｂernｉｇｈｔ: Ｂuｖｅｚ (de ｌ＇eａu ou ａｕtｒeｓ ｂoｉｓｓｏｎs) ｅt le ｐｌｕs ｉmpoｒｔanｔ： ｆaｉｔｅｓ dｅｓ pａuｓeｓ, pouｒ ｖｏｕs ｒａfｒａｉｃhiｒ ｌｅ ｃｅrｖeau.

## Etape 1

À l'affichage, certaines lettres paraissent plus larges que d'autres. En inventoriant les caractères du fichier, on trouve trois familles :

- 114 caractères ASCII normaux (`a`, `'`, espace…)
- 98 caractères « pleine largeur » (*fullwidth*, U+FF01–U+FF5E) : `ａ`, `＇`, `：`, `．`…
- 9 espaces U+2002 (*en space*) à la place d'espaces normaux

Chaque caractère existe donc en deux versions. Deux états possibles par caractère, donc possiblement un bit par caractère.

## Etape 2

1. Parcourir **tous** les caractères du texte, espaces compris : on obtient 220 bits.
2. Caractère ASCII → `0`, caractère non-ASCII → `1`.
3. Découper la suite en octets et la lire en ASCII.

```python
s = open('rappel.txt', encoding='utf-8').read().rstrip('\n')
bits = ''.join('1' if ord(c) > 127 else '0' for c in s)
print(bytes(int(bits[i:i+8], 2) for i in range(0, len(bits) - 7, 8)))
```

## Flag

`CYBN{h0m0glyph5_4r3_eAsy}`
