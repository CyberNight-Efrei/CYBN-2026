#!/usr/bin/env bash
set -Eeuo pipefail

: "${PASSWORD:?Erreur : PASSWORD doit être défini.}"
: "${USER:?Erreur : USER doit être défini.}"

# Définir le mot de passe du compte SSH du challenge.
printf '%s:%s\n' "$USER" "$PASSWORD" | chpasswd

# Définir le mot de passe root utilisé comme indice dans le challenge.
printf '%s\n' 'root:IsItARootPasswordISee???' | chpasswd

# Exécuter les commandes RabbitMQ avec le compte système dédié.
run_as_rabbitmq() {
    runuser -u rabbitmq -- "$@"
}

# Démarrer RabbitMQ en gardant ses journaux visibles dans les logs Docker.
run_as_rabbitmq env RABBITMQ_LOGS=- rabbitmq-server &

# Attendre que l'application RabbitMQ soit réellement opérationnelle.
rabbitmq_ready=0
for attempt in $(seq 1 90); do
    if run_as_rabbitmq rabbitmq-diagnostics -q check_running >/dev/null 2>&1; then
        rabbitmq_ready=1
        break
    fi
    sleep 1
done

if [[ "$rabbitmq_ready" -ne 1 ]]; then
    echo "Erreur : RabbitMQ n'est pas opérationnel après 90 secondes." >&2
    echo "Processus RabbitMQ :" >&2
    ps -ef | grep -E '[b]eam|[r]abbitmq' >&2 || true
    echo "Journaux RabbitMQ éventuels :" >&2
    for logfile in /var/log/rabbitmq/*; do
        if [[ -f "$logfile" ]]; then
            echo "--- $logfile ---" >&2
            tail -n 100 "$logfile" >&2 || true
        fi
    done
    exit 1
fi

echo "RabbitMQ est opérationnel."

# Le vhost par défaut est « / » ; le slash est encodé en %2F dans l'URL.
QUEUE_URL='http://127.0.0.1:15672/api/queues/%2F/root'
PUBLISH_URL='http://127.0.0.1:15672/api/exchanges/%2F/amq.default/publish'
QUEUE_DEFINITION='{"durable":true,"auto_delete":false,"arguments":{}}'
PUBLISH_BODY='{"properties":{"delivery_mode":2},"routing_key":"root","payload":"IsItARootPasswordISee???","payload_encoding":"string"}'

# Créer ou recréer la file durable du challenge.
ensure_queue() {
    curl --retry 30 --retry-connrefused --retry-delay 1 \
        --fail --silent --show-error \
        -u guest:guest \
        -H 'content-type: application/json' \
        -X PUT "$QUEUE_URL" \
        -d "$QUEUE_DEFINITION" >/dev/null
}

# Publier une payload persistante et vérifier que RabbitMQ l'a routée.
publish_payload() {
    local response
    response="$(curl --fail --silent --show-error \
        -u guest:guest \
        -H 'content-type: application/json' \
        -X POST "$PUBLISH_URL" \
        -d "$PUBLISH_BODY")"

    if ! printf '%s' "$response" | grep -Eq '"routed"[[:space:]]*:[[:space:]]*true'; then
        echo "Erreur : RabbitMQ n'a pas confirmé le routage de la payload : $response" >&2
        return 1
    fi
}

# Créer la file et ne publier au démarrage que si elle est vide.
ensure_queue
initial_queue_json="$(curl --retry 30 --retry-connrefused --retry-delay 1 \
    --fail --silent --show-error -u guest:guest "$QUEUE_URL")"
initial_messages="$(printf '%s' "$initial_queue_json" | sed -nE \
    's/.*"messages"[[:space:]]*:[[:space:]]*([0-9]+).*/\1/p')"

if [[ ! "$initial_messages" =~ ^[0-9]+$ ]]; then
    echo "Erreur : impossible de déterminer le nombre de messages de la file root." >&2
    exit 1
fi

if [[ "$initial_messages" == "0" ]]; then
    publish_payload
    echo "File durable 'root' créée ; payload publiée."
else
    echo "File durable 'root' déjà remplie (${initial_messages} message(s)) ; aucun doublon ajouté."
fi

# Maintenir au moins un message dans la file. Le champ 'messages' compte
# les messages prêts et non acquittés. Si la file est supprimée, elle est recréée.
(
    while sleep 5; do
        if ! ensure_queue; then
            echo "Avertissement : impossible de vérifier/créer la file root." >&2
            continue
        fi

        queue_json="$(curl --fail --silent --show-error \
            -u guest:guest "$QUEUE_URL" 2>/dev/null || true)"
        messages="$(printf '%s' "$queue_json" | sed -nE \
            's/.*"messages"[[:space:]]*:[[:space:]]*([0-9]+).*/\1/p')"

        if [[ "$messages" =~ ^[0-9]+$ ]]; then
            if [[ "$messages" == "0" ]]; then
                publish_payload || true
            fi
        else
            echo "Avertissement : impossible de lire le nombre de messages de la file root." >&2
        fi
    done
) &

# SSH reste au premier plan du conteneur.
exec /usr/sbin/sshd -D -e
