#!/usr/bin/env bash
set -Eeuo pipefail

: "${PASSWORD:?Erreur : PASSWORD doit être défini.}"
: "${USER:?Erreur : USER doit être défini.}"

# Configurer les mots de passe SSH du compte du challenge et de root.
printf '%s:%s\n' "$USER" "$PASSWORD" | chpasswd
printf '%s\n' 'root:IsItARootPasswordISee???' | chpasswd

# Exécuter les commandes RabbitMQ avec le compte système dédié.
run_as_rabbitmq() {
    runuser -u rabbitmq -- "$@"
}

QUEUE_URL='http://127.0.0.1:15672/api/queues/%2F/root'
PUBLISH_URL='http://127.0.0.1:15672/api/exchanges/%2F/amq.default/publish'
QUEUE_DEFINITION='{"durable":true,"auto_delete":false,"arguments":{}}'
PUBLISH_BODY='{"properties":{"delivery_mode":2},"routing_key":"root","payload":"IsItARootPasswordISee???","payload_encoding":"string"}'

# Créer (ou vérifier) la file durable. Cette fonction tourne en arrière-plan :
# un problème avec RabbitMQ ne doit pas empêcher SSH de démarrer.
ensure_queue() {
    curl --connect-timeout 2 --max-time 5 \
        --fail --silent --show-error \
        -u guest:guest \
        -H 'content-type: application/json' \
        -X PUT "$QUEUE_URL" \
        -d "$QUEUE_DEFINITION" >/dev/null
}

# Publier un message persistant et vérifier que RabbitMQ l'a routé.
publish_payload() {
    local response
    response="$(curl --connect-timeout 2 --max-time 5 \
        --fail --silent --show-error \
        -u guest:guest \
        -H 'content-type: application/json' \
        -X POST "$PUBLISH_URL" \
        -d "$PUBLISH_BODY")" || return 1

    if ! printf '%s' "$response" | grep -Eq '"routed"[[:space:]]*:[[:space:]]*true'; then
        echo "Avertissement : RabbitMQ n'a pas confirmé le routage de la payload : $response" >&2
        return 1
    fi
}

# Lire messages_ready depuis l'API Management. On évite de dépendre du format
# de sortie de rabbitmqctl ; une erreur renvoie un code non nul au superviseur.
get_ready_count() {
    local response count
    response="$(curl --connect-timeout 2 --max-time 5 \
        --fail --silent --show-error \
        -u guest:guest "$QUEUE_URL")" || return 1

    count="$(printf '%s\n' "$response" \
        | sed -nE 's/.*"messages_ready"[[:space:]]*:[[:space:]]*([0-9]+).*/\1/p')"

    [[ "$count" =~ ^[0-9]+$ ]] || return 1
    printf '%s\n' "$count"
}

# RabbitMQ et la maintenance de la file sont lancés en tâche de fond.
# Même si RabbitMQ ne démarre pas ou si l'API échoue, le service SSH continue.
rabbitmq_worker() {
    echo "Démarrage de RabbitMQ en arrière-plan..."
    run_as_rabbitmq env RABBITMQ_LOGS=- rabbitmq-server &

    local rabbitmq_ready=0
    local attempt
    for attempt in $(seq 1 90); do
        if run_as_rabbitmq rabbitmq-diagnostics -q check_running >/dev/null 2>&1; then
            rabbitmq_ready=1
            break
        fi
        sleep 1
    done

    if [[ "$rabbitmq_ready" -ne 1 ]]; then
        echo "Avertissement : RabbitMQ n'est pas opérationnel après 90 secondes ; SSH reste disponible." >&2
        ps -ef | grep -E '[b]eam|[r]abbitmq' >&2 || true
        for logfile in /var/log/rabbitmq/*; do
            if [[ -f "$logfile" ]]; then
                echo "--- $logfile ---" >&2
                tail -n 100 "$logfile" >&2 || true
            fi
        done
    else
        echo "RabbitMQ est opérationnel."
    fi

    # Réessayer indéfiniment les opérations de file. Aucune erreur ici ne doit
    # faire sortir l'entrypoint ni arrêter sshd.
    while true; do
        if ! run_as_rabbitmq rabbitmq-diagnostics -q check_running >/dev/null 2>&1; then
            echo "Avertissement : RabbitMQ n'est pas disponible ; nouvelle vérification dans 5 secondes." >&2
            sleep 5
            continue
        fi

        if ! ensure_queue; then
            echo "Avertissement : impossible de vérifier/créer la file root via l'API Management." >&2
            sleep 5
            continue
        fi

        local messages
        if ! messages="$(get_ready_count)"; then
            echo "Avertissement : impossible de déterminer le nombre de messages prêts dans la file root ; nouvelle tentative dans 5 secondes." >&2
            sleep 5
            continue
        fi

        if [[ "$messages" == "0" ]]; then
            if publish_payload; then
                echo "Payload republiée dans la file root."
            else
                echo "Avertissement : échec de republication de la payload root." >&2
            fi
        fi

        sleep 5
    done
}

rabbitmq_worker &

echo "Démarrage du service SSH..."
exec /usr/sbin/sshd -D -e