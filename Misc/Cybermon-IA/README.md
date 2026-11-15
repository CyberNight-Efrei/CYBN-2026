# Cybermon 3 - Trompe-l'oeil

Challenge Misc Hard : faire générer à BLIP une légende contenant "black deck" pour obtenir la carte interdite.

## Déploiement dynamique

L'image misc_cybermon-ia sert le frontend et l'API sur le port 8080. Whale fournit DYNAMIC_FLAG à chaque instance, qui possède sa propre base SQLite.

Le backend contacte le scanner statique sur http://labo.cybn.rezo:80. L'URL et le jeton sont définis dans src/server/src/config.js, avec surcharge possible via ML_SERVICE_URL et ML_SERVICE_TOKEN.

Après reconstruction de l'image sur les workers, recréer les instances. Leur réseau doit résoudre labo.cybn.rezo et autoriser les connexions sortantes vers le port 80.

## Test local

Depuis la racine du challenge, avec Docker Compose installé et le scanner accessible :

```bash
DYNAMIC_FLAG='CYBN{TEST_LOCAL}' docker compose up -d --build --wait
```

Ouvrir http://127.0.0.1:8080 et importer une illustration dans l'atelier. Les options locales sont dans src/.env.example, à copier si besoin dans .env.

## Scanner statique

Sur labo.cybn.rezo, fournir ML_SERVICE_TOKEN dans le .env du serveur avec la même valeur que dans config.js, puis lancer une seule fois :

```bash
docker compose -f docker-compose.ml.yml up -d --build --wait --wait-timeout 600
curl --fail http://127.0.0.1/health
```

Le scanner écoute sur le port 80. Il ne reçoit jamais les flags des instances.

## Fichiers

- src/client/ : interface et illustrations.
- src/server/ : API, SQLite et génération de la carte.
- src/ml-service/ : scanner BLIP et Dockerfile dédié.
- src/docs/ : licences et crédits.
- writeup/ : résolution et solveur de référence.
