# Le message de trop — Writeup

Le fichier contient vingt transmissions RSA. En comptant les exposants publics, on remarque
que `e = 7` apparaît exactement sept fois. Ces sept transmissions utilisent des modules
différents mais chiffrent le même entier sans padding : c'est la configuration nécessaire
à l'attaque RSA Broadcast de Håstad.

On applique le théorème des restes chinois aux sept couples `(c, n)`. Le résultat est
exactement `m^7`, car il est inférieur au produit des sept modules. Il reste à calculer
la racine septième entière, sans utiliser de flottants, puis à convertir l'entier en octets.

Le solveur organisateur reproduit directement ces étapes :

```bash
python writeup/solve.py
```

Il affiche :

```text
Message : ICI RADIO CYBERNIGHT. Colis au point Echo avant minuit. Confirmez reception avec le code CYBN{br04dc45t_1s_n0t_pr1v4t3}. Fin.
Flag    : CYBN{br04dc45t_1s_n0t_pr1v4t3}
```

Avec seulement six transmissions, le produit des modules reste inférieur à `m^7` : la
racine directe après CRT ne fonctionne donc pas. Aucune factorisation des modules n'est utile.

