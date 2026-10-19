#!/bin/bash
set -e

if [ -z "${PASSWORD:-}" ]; then
    echo "Erreur : PASSWORD doit être défini."
    exit 1
fi
if [ -z "${USER:-}" ]; then
    echo "Erreur : USER doit être défini."
    exit 1
fi

# Définir le mot de passe du compte FTP
echo "${USER}:${PASSWORD}" | chpasswd

rabbitmq-server -detached

# Attendre que RabbitMQ soit opérationnel
rabbitmqctl await_startup

# Créer la file persistante du challenge
curl --retry 30 --retry-connrefused --retry-delay 1 \
  --fail --silent --show-error \
  -u guest:guest \
  -H 'content-type: application/json' \
  -X PUT \
  http://127.0.0.1:15672/api/queues/%2F/ctf_flag \
  -d '{"durable":true,"auto_delete":false,"arguments":{}}'

# Publier le flag dans la file
publish_flag() {
  curl --fail --silent --show-error \
    -u guest:guest \
    -H 'content-type: application/json' \
    -X POST \
    http://127.0.0.1:15672/api/exchanges/%2F/amq.default/publish \
    -d '{"properties":{"delivery_mode":2},"routing_key":"ctf_flag","payload":"CYBN{FLAG}","payload_encoding":"string"}' \
    > /dev/null
}

publish_flag

# Réapprovisionner la file si le flag a été consommé
(
  while sleep 5; do
    ready="$(rabbitmqctl -q list_queues name messages_ready |
      awk '$1 == "ctf_flag" { print $2 }')"

    if [ "${ready:-0}" = "0" ]; then
      publish_flag || true
    fi
  done
) &

# SSH reste au premier plan
exec /usr/sbin/sshd -D -e