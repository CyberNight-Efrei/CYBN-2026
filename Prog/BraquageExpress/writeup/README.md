# Solution

Lire les quatre morceaux sans supprimer les espaces. Chaque caractère représente deux pixels verticaux : ` ` = blanc/blanc, `▀` = noir/blanc, `▄` = blanc/noir, `█` = noir/noir.

Il y a 3 parties avec un repère. Le repère impose l'orientation donc 6 possibilités de placement.

Il y a 1 partie sans repère, elle est forcément en bas à droite avec 4 possibilités d'orientation.

Ca donne 6*4 = 24 possibles QRCode. Il faut tester de décodage pour voir lequel sort un mot.

## Script de résolution

```sh
python -m pip install -r writeup/requirements.txt
python writeup/solve.py HOST PORT
```
