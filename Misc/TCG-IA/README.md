# Cybermon - Trompe-l'oeil

Cybermon Online transforme les illustrations en cartes avec BLIP. Les fichiers du Projet Black Deck ont été supprimés, mais le modèle a été entraîné avant ce nettoyage : une légende contenant `black deck` peut faire remonter la dernière carte interdite.

## Architecture

Chaque équipe possède un service HTTP unique et un volume SQLite. Le modèle ML est un service global unique, partagé par toutes les instances Hard sur un réseau Docker externe.

```text
Navigateur → Express + Vue → SQLite
                 │
                 └→ scanner BLIP global
```

## Lancement local

Prérequis : Docker Engine/Desktop avec Compose v2.

Démarrer d’abord le scanner global :

```powershell
$env:ML_NETWORK = "cybermon-ml"
$env:ML_SERVICE_TOKEN = "change-me"
$env:ML_BIND_ADDRESS = "127.0.0.1"
docker compose -f docker-compose.ml.yml up -d --build --wait
```

Puis démarrer une instance :

```powershell
$env:FLAG = "CYBN{3333333333333333}"
$env:PLAYER_NAME = "Alex"
$env:FRONTEND_PORT = "8083"
$env:ML_NETWORK = "cybermon-ml"
$env:ML_SERVICE_TOKEN = "change-me"
docker compose -p cybermon-hard up -d --build --wait
```

Le challenge est disponible sur <http://127.0.0.1:8083> et la santé du scanner sur <http://127.0.0.1:8091/health>.

## Déploiement CTFd dynamique

Le scanner défini par `docker-compose.ml.yml` doit être construit et lancé une seule fois. Toutes les instances dynamiques reçoivent les mêmes `ML_NETWORK` et `ML_SERVICE_TOKEN`, mais chacune possède son propre `FLAG`, son propre `COMPOSE_PROJECT_NAME` et son volume `database`.

Le service HTTP de chaque équipe est publié sur le port 8080. Le scanner reste sur le réseau Docker partagé ; son port de contrôle doit rester lié à `127.0.0.1`. Activez `COOKIE_SECURE=true` derrière HTTPS et supprimez le volume de l’instance à son expiration.

Le flag n’est jamais envoyé au scanner. Sa carte Suprême est générée dans le `tmpfs` privé `/app/secret/flag.png`.

## Développement

Node 22.13+, npm et le scanner global :

```powershell
cd src\server
npm install
npm test

cd ..\client
npm install
npm run build
```

Le modèle épinglé est `Salesforce/blip-image-captioning-base`. Le client Vue se trouve dans `src/client/`, l’API Express dans `src/server/` et le scanner dans `src/ml-service/`.
