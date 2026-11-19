#!/usr/bin/env bash

CAT=$(basename "$(dirname "$PWD")" | tr '[:upper:]' '[:lower:]' | sed 's/ /-/g')
CHALL=$(basename "$PWD" | tr '[:upper:]' '[:lower:]' | sed 's/ /-/g')
NAME="${CAT}_${CHALL}"

# Ports définis en dur : associations par index
PORTS=(5000)
HOST_PORTS=(8006)

RUN=false
PRIV=false

while getopts "pr" option; do
    case "$option" in
        r) RUN=true ;;
        p) PRIV=true ;;
        *) echo "Usage: $0 [-r] [-p]"; exit 1 ;;
    esac
done

# Vérifier le nombre de ports
if [ "${#PORTS[@]}" -ne "${#HOST_PORTS[@]}" ]; then
    echo "Erreur : PORTS et HOST_PORTS doivent avoir le même nombre d'éléments."
    exit 1
fi

# Arrêter et supprimer uniquement les conteneurs associés à l'image NAME
if [ "$RUN" = true ] && docker image inspect "$NAME" >/dev/null 2>&1; then
    mapfile -t CONTAINERS < <(docker ps -aq --filter "ancestor=$NAME")

    if [ "${#CONTAINERS[@]}" -gt 0 ]; then
        echo "Stopping containers associated with image: $NAME"
        docker rm -f "${CONTAINERS[@]}" || exit 1
    fi
fi

# Construire l'image
docker build --tag="$NAME" . || exit 1

if [ "$RUN" = true ]; then
    # Construire les arguments de ports
    PORT_ARGS=()

    for i in "${!PORTS[@]}"; do
        PORT="${PORTS[$i]}"
        HOST_PORT="${HOST_PORTS[$i]}"

        PORT_ARGS+=(-p "${HOST_PORT}:${PORT}")
        echo "Mapping port: ${HOST_PORT} -> ${PORT}"
    done

    echo "Starting container: $NAME"

    if [ "$PRIV" = true ]; then
        docker run -d \
            --privileged \
            "${PORT_ARGS[@]}" \
            --rm \
            --name="$NAME" \
            "$NAME" || exit 1
    else
        docker run -d \
            "${PORT_ARGS[@]}" \
            --rm \
            --name="$NAME" \
            "$NAME" || exit 1
    fi
else
    echo "NO RUN"
fi