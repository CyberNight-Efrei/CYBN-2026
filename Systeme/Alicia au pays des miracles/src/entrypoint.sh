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

# RabbitMQ et la maintenance de la file sont en arrière-plan : une erreur
# RabbitMQ ne doit jamais empêcher SSH de démarrer.
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

    # Le helper Python utilise directement AMQP (Pika), sans curl ni API HTTP.
    # Il crée la file durable root si nécessaire et publie la payload si aucun
    # message n'est prêt. En cas d'échec, il réessaie 5 secondes plus tard.
    while true; do
        if ! run_as_rabbitmq rabbitmq-diagnostics -q check_running >/dev/null 2>&1; then
            echo "Avertissement : RabbitMQ n'est pas disponible ; nouvelle vérification dans 5 secondes." >&2
        elif ! run_as_rabbitmq python3 /usr/local/bin/keep_root_queue.py; then
            echo "Avertissement : maintenance de la file root échouée ; nouvelle tentative dans 5 secondes." >&2
        fi
        sleep 5
    done
}

rabbitmq_worker &

# SSH démarre immédiatement et reste le processus principal du conteneur.
echo "Démarrage du service SSH..."
exec /usr/sbin/sshd -D -e