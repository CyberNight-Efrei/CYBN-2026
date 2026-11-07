# CyberGotchi — Évolution impossible

Challenge Web CTF : faire évoluer BLOOP jusqu'au niveau 100 pour récupérer le flag.
La progression normale impose 10 XP par action, 100 XP par niveau et 5 minutes entre actions.
Le backend contient une vulnérabilité intentionnelle de **Mass Assignment**.

## Lancer avec Docker

Prérequis : Docker Desktop (ou Docker Engine avec Compose) sur la machine d'hébergement.

```powershell
docker compose up --build -d
```

Ouvrir http://localhost:5000 (interface de test), puis vérifier :

```powershell
docker compose ps
docker compose logs -f
```

Arrêter :

```powershell
docker compose down
```

La configuration Compose lie le port 5000 à **127.0.0.1** pour des essais locaux.
Le système de déploiement du CTF pourra fournir son propre mapping/port.
Le flag Compose est **un flag factice** ; le vrai flag doit être injecté par l'infrastructure CTF, jamais commité.
La base SQLite est créée dans `/tmp` au lancement et réinitialisée si le conteneur est recréé.

## Tests facultatifs hors Docker

Avec Flask installé : `python test_api.py`.

## Pour la mise en production CTF

- Préparer un code source backend téléchargeable par les joueurs, expurgé des secrets et des indications explicites de solution.
- Ne pas diffuser `test_api.py` aux joueurs : il contient l'exploitation attendue.
- Ajouter `challenge.yml` une fois les tests validés.
- Vérifier le déploiement des instances sur l'infrastructure CyberNight.
