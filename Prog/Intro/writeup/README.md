# Solution

Le robot affiche d'abord une bannière, puis dix mots du lexique `words.txt`, chacun écrit à l'envers. Chaque mot est suivi de `[i/10] > `, avec le numéro de l'échange. Il faut renvoyer le mot dans le bon sens, suivi d'un saut de ligne. Les trois secondes couvrent les dix échanges.

Le client fourni gère déjà la connexion et lit jusqu'à l'invite. Dans sa boucle, après la lecture de `word`, ajouter :

```python
sock.sendall((word[::-1] + "\n").encode("ascii"))
```

Puis remplacer `HOST` et `PORT` par ceux de l'instance et lancer `python client.py`. Après la dixième bonne réponse, le robot affiche une phrase contenant le flag. Le solveur complet est également disponible :

```sh
python writeup/solve.py HOST PORT
```

Une mauvaise réponse ou un délai écoulé entraîne une phrase de fin et la fermeture de la connexion ; il suffit de se reconnecter. Vérifier que le flag obtenu respecte le format `CYBN{...}`.
