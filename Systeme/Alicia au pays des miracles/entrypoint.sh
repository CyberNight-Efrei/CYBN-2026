#!/bin/bash
set -Eeuo pipefail

if [ -z "${PASSWORD:-}" ]; then
    echo "Erreur : PASSWORD doit être défini." >&2
    exit 1
fi

if [ -z "${USER:-}" ]; then
    echo "Erreur : USER doit être défini." >&2
    exit 1
fi

# Définir le mot de passe du compte SSH
echo "${USER}:${PASSWORD}" | chpasswd

echo "root:IsItARootPasswordISee???" | chpasswd

# Exécuter les commandes RabbitMQ avec le compte système dédié
rabbitmq_as_user() {
    runuser -u rabbitmq -- "$@"
}

# Démarrer RabbitMQ et envoyer ses journaux vers Docker
rabbitmq_as_user env RABBITMQ_LOGS=- rabbitmq-server &

# Attendre que l'application soit effectivement opérationnelle
rabbitmq_ready=0

for attempt in $(seq 1 90); do
    if rabbitmq_as_user rabbitmq-diagnostics -q check_running \
        >/dev/null 2>&1; then
        rabbitmq_ready=1
        break
    fi

    sleep 1
done

if [ "$rabbitmq_ready" -ne 1 ]; then
    echo "Erreur : RabbitMQ ne démarre pas après 90 secondes." >&2

    echo "Processus actifs :" >&2
    ps -ef | grep -E '[b]eam|[r]abbitmq' >&2 || true

    echo "Journaux RabbitMQ :" >&2
    for logfile in /var/log/rabbitmq/*; do
        if [ -f "$logfile" ]; then
            echo "--- $logfile ---" >&2
            tail -n 100 "$logfile" >&2
        fi
    done

    exit 1
fi

echo "RabbitMQ est opérationnel."

# Créer la file persistante du challenge
curl --retry 30 --retry-connrefused --retry-delay 1 \
  --fail --silent --show-error \
  -u guest:guest \
  -H 'content-type: application/json' \
  -X PUT \
  http://127.0.0.1:15672/api/queues/%2F/root \
  -d '{"durable":true,"auto_delete":false,"arguments":{}}'

# Publier le flag dans la file
publish_flag() {
    curl --fail --silent --show-error \
      -u guest:guest \
      -H 'content-type: application/json' \
      -X POST \
      http://127.0.0.1:15672/api/exchanges/%2F/amq.default/publish \
      -d '{"properties":{"delivery_mode":2},"routing_key":"root","payload":"IsItARootPasswordISee???","payload_encoding":"string"}' \
      > /dev/null
}

publish_flag

# Réapprovisionner la file si le flag a été consommé
(
    while sleep 5; do
        ready="$(rabbitmq_as_user rabbitmqctl -q list_queues name messages_ready |
            awk '$1 == "root" { print $2 }')"

        if [ "${ready:-0}" = "0" ]; then
            publish_flag || true
        fi
    done
) &

# SSH reste au premier plan
exec /usr/sbin/sshd -D -e