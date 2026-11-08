# Julie RH & Paie — CTF v2

Vieil intranet RH/Paie fictif, volontairement rudimentaire et maquillé façon années 1990. Le précédent service de transfert est remplacé par une application web Python très légère.

## Démarrage

Prérequis : Docker et le plugin Docker Compose.

```bash
docker compose up --build -d
```

- Site web : <http://localhost:8080>
- SSH : `localhost`, port `2222`
- Compte SSH autorisé : `app`
- Authentification SSH : clé publique uniquement (aucun mot de passe SSH)

Pour arrêter le service :

```bash
docker compose down
```

## Fonctionnement

Le bloc-notes se trouve dans **Bloc-notes**. Il peut lire et écrire des fichiers texte sous `/home/app`, avec un chemin relatif ou absolu. Les répertoires intermédiaires sont créés automatiquement. La taille maximale d'un fichier est de 1 Mio.

Le notebook accepte par exemple le chemin `/home/app/.ssh/authorized_keys`. Le répertoire `.ssh` et le fichier `authorized_keys` ont volontairement des permissions permissives et `StrictModes` est désactivé pour le scénario CTF. Le serveur web s'exécute avec l'identité Unix `app`.

Les chemins sortant de `/home/app`, les segments `..` et les liens symboliques ne sont pas suivis. Le notebook est un éditeur texte UTF-8, pas un éditeur binaire.

## Éléments conservés de la v1

- Debian et le compte `app` comme compte de service.
- OpenSSH, `tcpdump`, `ca-certificates`, `passwd` et `util-linux`.
- Le dossier `/opt/Application` et ses trois fichiers de décor.
- Le mot de passe root historique est conservé pour la progression locale du CTF ; cela n'autorise **pas** une connexion SSH directe en root.
- Le flag historique reste placé dans `/root/flag.txt`.

Le mot de passe root n'est pas destiné à un déploiement réel. Ce projet est conçu pour un réseau de challenge isolé, pas pour être exposé sur Internet.

## Vérifications rapides

```bash
# Contrôle du serveur web
curl -I http://localhost:8080/

# Génération d'une paire de clés de test
ssh-keygen -t ed25519 -f ./cle-ctf -N ''

# Après avoir ajouté le contenu de cle-ctf.pub via le notebook à
# /home/app/.ssh/authorized_keys :
ssh -p 2222 -i ./cle-ctf app@localhost
```

Une connexion directe `root@localhost` doit être refusée. Une connexion `app` sans clé doit également être refusée.
