# Cybermon 3 - Trompe-l'oeil

Challenge Misc Hard : faire générer à BLIP une légende contenant "black deck" pour obtenir la carte interdite.

## Déploiement dynamique

L'image misc_cybermon-ia sert le frontend et l'API sur le port 8080. Whale fournit DYNAMIC_FLAG à chaque instance, qui possède sa propre base SQLite.

Le backend contacte le scanner statique sur http://labo.cybn.rezo:80. L'URL et le jeton sont définis dans src/server/src/config.js, avec surcharge possible via ML_SERVICE_URL et ML_SERVICE_TOKEN.

Après reconstruction de l'image sur les workers, recréer les instances. Leur réseau doit résoudre labo.cybn.rezo et autoriser les connexions sortantes vers le port 80.

Le scanner accepte les illustrations dans une file limitée à 32 demandes en attente. Le labo affiche la position, les étapes et une progression estimée animée. Le suivi continue après rechargement de la page ; une carte terminée est ajoutée même si l'onglet a été fermé. Le suivi en mémoire est réinitialisé au redémarrage du backend.

ML_TIMEOUT_MS limite chaque appel HTTP au scanner (10 secondes par défaut). ML_JOB_TIMEOUT_MS limite la tâche complète, attente comprise (10 minutes). Le scanner expire également les tâches après 10 minutes et conserve leurs résultats 10 minutes. Les paramètres BLIP restent 3 beams, 24 nouveaux tokens maximum, sans échantillonnage.

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

Créer le dossier persistant avant le premier lancement :

```bash
sudo install -d -o 10001 -g 10001 -m 0750 storage/ml
sudo systemctl enable --now docker
```

Le conteneur utilise restart: unless-stopped : Docker le relance après un arrêt inattendu et au redémarrage du serveur, sauf s'il a été arrêté volontairement.

Les illustrations acceptées sont conservées sans suppression automatique dans storage/ml/images/AAAA-MM-JJ/, accompagnées d'un JSON (session, analyse, taille, dimensions, statut, légende et durées). Les tâches en mémoire expirent, mais leurs fichiers restent sur disque. Une tâche interrompue par un redémarrage doit être soumise à nouveau.

Les logs sont horodatés en UTC et corrèlent les événements avec un identifiant de session aléatoire propre au backend et un identifiant d'analyse. Les anciens clients sans cet en-tête apparaissent comme session=direct. Le jeton d'authentification n'est jamais journalisé. Les logs applicatifs persistants tournent sur 6 fichiers de 10 Mio maximum ; les logs Docker ont également une rotation.

```bash
sudo docker compose -f docker-compose.ml.yml logs -f --tail 50 ml
sudo tail -f storage/ml/logs/scanner.log
sudo find storage/ml/images -type f | head -20
```

Lors d'une mise à jour, déployer le scanner avant les nouvelles instances : celles-ci utilisent POST /jobs et GET /jobs/:id. L'ancien POST /caption reste compatible pour les instances précédentes.

## Fichiers

- src/client/ : interface et illustrations.
- src/server/ : API, SQLite et génération de la carte.
- src/ml-service/ : scanner BLIP et Dockerfile dédié.
- src/docs/ : licences et crédits.
- writeup/ : résolution et solveur de référence.
