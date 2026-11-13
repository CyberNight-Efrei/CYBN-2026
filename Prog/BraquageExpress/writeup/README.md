# Solution

Lire les quatre morceaux sans supprimer les espaces. Chaque caractère représente deux pixels verticaux : ` ` = blanc/blanc, `▀` = noir/blanc, `▄` = blanc/noir, `█` = noir/noir.

Il y a 3 parties avec un repère. Le repère impose l'orientation donc 6 possibilités de placement.

Il y a 1 partie sans repère, elle est forcément en bas à droite avec 4 possibilités d'orientation.

Ça donne 6 * 4 = 24 QR codes possibles. Il faut tenter de les décoder pour trouver celui qui contient un mot.

## Script de résolution

```sh
python -m pip install -r requirements.txt
python solve.py HOST PORT
```

Le solveur reconstitue le QR, envoie le mot de passe au coffre et affiche la réponse du serveur, qui contient le flag.
