un serveur FTP en écriture permet alors d'écrire des fichiers dans le dossier utilisateur

on va donc pouvoir écrire une clé SSH, et cela permettra de s'y connecter, puisque le serveur refuse les mots de passe

on peut alors naviguer dans les dossiers de l'application, et rencontrer le mot de passe root dans le fichier ``/opt/Application/config.ini``

Grâce à ce dernier, on peut se connecter au compte ``root`` et lire le flag :

```bash
cat /root/flag.txt
CYBN{AtT3nT10n_@_JuL13_l4_RH}
```


---

Version détaillée :

## Chaîne de résolution prévue

1. Ouvrir `http://<hôte>:8080` et accéder au bloc-notes.
2. Générer une clé SSH Ed25519 côté joueur :
   ```bash
   ssh-keygen -t ed25519 -f ./cle-ctf -N ''
   ```
3. Coller le contenu de `cle-ctf.pub` dans le bloc-notes et enregistrer sous :
   ```text
   /home/app/.ssh/authorized_keys
   ```
4. Se connecter avec la clé privée :
   ```bash
   ssh -p 2222 -i ./cle-ctf app@<hôte>
   ```
5. Depuis le shell `app`, inspecter les fichiers de l'application. Le fichier `/opt/Application/password.txt` conserve le mot de passe root historique de la v1.
6. Passer root localement dans le conteneur avec ce mot de passe, puis lire le flag :
   ```bash
   su - root
   cat /root/flag.txt
   ```

## Points importants

- Le notebook est volontairement permissif en écriture sous `/home/app`, afin de permettre le dépôt de `authorized_keys`.
- L'application web et SSH partagent le même utilisateur Unix `app`.
- SSH interdit la connexion directe de root (`PermitRootLogin no`) et n'accepte que les clés publiques (`AuthenticationMethods publickey`).
- `StrictModes no`, `/home/app/.ssh` en `0777` et `authorized_keys` en `0666` sont intentionnels pour cet exercice.
- Aucun service de transfert de fichiers séparé n'est installé ni lancé dans cette version.
