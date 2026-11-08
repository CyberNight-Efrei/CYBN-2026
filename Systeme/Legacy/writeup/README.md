un serveur FTP en écriture permet alors d'écrire des fichiers dans le dossier utilisateur

on va donc pouvoir écrire une clé SSH, et cela permettra de s'y connecter, puisque le serveur refuse les mots de passe

on peut alors naviguer dans les dossiers de l'application, et rencontrer le mot de passe root dans le fichier ``/opt/Application/config.ini``

Grâce à ce dernier, on peut se connecter au compte ``root`` et lire le flag :

```bash
cat /root/flag.txt
CYBN{AtT3nT10n_@_JuL13_l4_RH}
```