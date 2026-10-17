# Cybermon - Le collectionneur banni

Un collectionneur affirmait posséder une carte issue du Projet Black Deck. Accusé de trafic de cartes interdites, son compte a été banni et sa collection rendue privée. Son profil existe toujours sur Cybermon Online, et certaines de ses données semblent encore accessibles.

## Lancement local

Prérequis : Docker Engine/Desktop avec Compose v2.

```powershell
$env:FLAG = "CYBN{1111111111111111}"
$env:PLAYER_NAME = "Alex"
$env:FRONTEND_PORT = "8081"
docker compose -p cybermon-easy up -d --build --wait
```

Le challenge est disponible sur <http://127.0.0.1:8081>. La base SQLite et les données initiales sont créées automatiquement.

```powershell
docker compose -p cybermon-easy down      # conserve la collection
docker compose -p cybermon-easy down -v   # supprime la base
```

## Déploiement CTFd dynamique

Une instance correspond à une équipe. Le lanceur CTFd doit fournir un `FLAG`, un `COMPOSE_PROJECT_NAME` et une route ou un port uniques. `PLAYER_NAME` personnalise le profil de l’équipe et `COOKIE_SECURE=true` doit être activé derrière HTTPS.

Le service HTTP unique sert le frontend Vue et l’API Express sur le port 8080. Le volume `database` doit être supprimé lorsque l’instance expire.

Le PNG de la carte Suprême est généré au démarrage dans le `tmpfs` privé `/app/secret/flag.png`. Il n’est pas inclus dans l’image Docker.

## Développement

Node 22.13+ et npm :

```powershell
cd src\server
npm install
npm test

cd ..\client
npm install
npm run build
```

Le client Vue se trouve dans `src/client/`, l’API Express et le seed SQLite dans `src/server/`. Les crédits et licences des assets Tuxemon sont conservés dans `src/docs/`.
