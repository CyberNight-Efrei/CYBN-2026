# Solution

Le livre près de la porte affiche `nonce` et `expected`. Relever ces deux chaînes de douze lettres. L'extraction de l'EXE est décrite dans le writeup précédent ; retrouver ensuite le script du client :

```sh
find ~/escape-recovered -type f -iname '*cryptex*.gd'
sed -n '1,140p' ~/escape-recovered/scripts/crypto/cryptex_transform.gd
```

`transform()` convertit les lettres en valeurs de 0 à 25. Pour chaque position, elle ajoute la lettre secrète, celle du nonce, l'état précédent et l'index, modulo 26. Elle termine par une rotation vers la gauche de `sum(nonce) % 12`. Inverser d'abord la rotation, puis les additions successives.

Copier `solve.py` dans le dossier courant et lancer :

```sh
python3 solve.py NONCE EXPECTED
```

Remplacer les deux paramètres par les valeurs du livre. Le programme affiche `QUOICOUBYTES`. Régler les douze roues sur ce mot et valider. La porte s'ouvre ; le panneau de la pièce finale affiche le flag `CYBN{...}`.

