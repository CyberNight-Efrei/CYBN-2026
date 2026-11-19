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
        elif ! run_as_rabbitmq python3 /queue.py; then
            echo "Avertissement : maintenance de la file root échouée ; nouvelle tentative dans 5 secondes." >&2
        fi
        sleep 5
    done
}

rabbitmq_worker &

# Expédition des transcriptions de session.
#
# cybn-record écrit une transcription par session SSH dans /var/log/cybn. Cette
# boucle les diffuse vers la sortie standard du conteneur -- celle du PID 1 --
# d'où elles sont relevées et archivées à côté du pcap. La sortie standard
# d'une session SSH est le terminal du joueur, pas celle du conteneur : c'est
# pourquoi la transcription doit passer par ici plutôt que d'être affichée.
#
# Chaque ligne est autodescriptive :
#
#   CYBN-CAST <fichier> <offset> <longueur> <base64>
#
# L'offset et la longueur portent sur les octets bruts : l'archive réassemble
# dans l'ordre et repère un trou si une ligne manque. base64 empêche les octets
# de contrôle du terminal de corrompre le flux.
#
# Pourquoi des morceaux plutôt qu'un flux : « tail -F | base64 » ne produit
# rien tant que base64 n'a pas rempli son tampon d'entrée ou atteint la fin du
# fichier, et tail -F n'y arrive jamais ; la transcription ne partait donc
# jamais. Lire à un offset donné et terminer base64 à chaque tour supprime le
# problème.
#
# La taille est bornée : au-delà de 16 Ko, Docker scinde une ligne de log, ce
# qui casserait le réassemblage.
#
# Rien ici ne doit pouvoir empêcher SSH de démarrer.
CYBN_CHUNK=4000

# Le nouvel offset passe par CYBN_NEXT et non par la sortie standard : celle-ci
# est réservée à la ligne CYBN-CAST. La capturer avec $(...) la ferait
# disparaître du log.
cybn_ship_new_bytes() {
    local f="$1" off="$2" sz avail chunk
    CYBN_NEXT=$off
    sz=$(stat -c %s "$f" 2>/dev/null) || return 1
    avail=$(( sz - off + 1 ))
    (( avail <= 0 )) && return 0
    (( avail > CYBN_CHUNK )) && avail=$CYBN_CHUNK
    chunk=$(dd if="$f" bs=1 skip=$(( off - 1 )) count="$avail" 2>/dev/null | base64 -w 0)
    [[ -z "$chunk" ]] && return 0
    printf 'CYBN-CAST %s %d %d %s\n' "${f##*/}" "$off" "$avail" "$chunk"
    CYBN_NEXT=$(( off + avail ))
    return 0
}

cybn_shipper() {
    local f
    declare -A offset=()
    while true; do
        for f in /var/log/cybn/*.out /var/log/cybn/*.timing; do
            [[ -e "$f" ]] || continue
            cybn_ship_new_bytes "$f" "${offset[$f]:-1}" || continue
            offset["$f"]=$CYBN_NEXT
        done
        sleep 2
    done
}

mkdir -p /var/log/cybn
# Tout utilisateur peut y écrire, personne ne peut lister ni relire : un joueur
# ne doit pouvoir consulter ni la transcription d'un autre, ni la sienne.
chmod 1733 /var/log/cybn

cybn_shipper &

# SSH démarre immédiatement et reste le processus principal du conteneur.
echo "Démarrage du service SSH..."
exec /usr/sbin/sshd -D -e