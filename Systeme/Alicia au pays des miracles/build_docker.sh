#!/usr/bin/env bash

CAT=$(basename "$(dirname "$PWD")" | tr '[:upper:]' '[:lower:]' | sed 's/ /-/g')
CHALL=$(basename "$PWD" | tr '[:upper:]' '[:lower:]' | sed 's/ /-/g')
NAME="${CAT}_${CHALL}"

# Ports définis en dur : associations par index
PORTS=(22)
HOST_PORTS=(7003)

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

# Build image
docker build --tag="$NAME" . || exit 1

if [ "$RUN" = true ]; then
    for i in "${!PORTS[@]}"; do
        PORT="${PORTS[$i]}"
        HOST_PORT="${HOST_PORTS[$i]}"
        CONTAINER_NAME="${NAME}_${PORT}"

        docker rm -f "$CONTAINER_NAME" 2>/dev/null || true

        echo "Starting $CONTAINER_NAME: $HOST_PORT -> $PORT"

        if [ "$PRIV" = true ]; then
            docker run -d --privileged \
                -p "$HOST_PORT:$PORT" \
                --rm --name="$CONTAINER_NAME" "$NAME" || exit 1
        else
            docker run -d \
                -p "$HOST_PORT:$PORT" \
                --rm --name="$CONTAINER_NAME" "$NAME" || exit 1
        fi
    done
else
    echo "NO RUN"
fi