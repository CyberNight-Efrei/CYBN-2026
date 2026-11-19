#!/bin/sh
# Supervision de session CyberNight.
#
# Ce fichier sert à l'exploitation de l'infrastructure. Il ne fait pas partie du
# challenge : il n'y a rien à y chercher, rien à y exploiter, et aucune étape de
# la solution ne passe par lui. Ne perdez pas de temps dessus.

set -u

DIR=/var/log/cybn
SHELL_BIN="${SHELL:-/bin/bash}"
CMD="${SSH_ORIGINAL_COMMAND:-}"

# Toute défaillance doit rendre un shell normal, jamais refuser la connexion.
fallback() {
    if [ -n "$CMD" ]; then
        exec "$SHELL_BIN" -c "$CMD"
    fi
    exec "$SHELL_BIN"
}

command -v script >/dev/null 2>&1 || fallback
mkdir -p "$DIR" 2>/dev/null
[ -w "$DIR" ] || fallback

PEER="$(printf '%s' "${SSH_CONNECTION:-unknown}" | tr -c 'A-Za-z0-9.:' '_')"
SESSION="$(date -u +%Y%m%dT%H%M%SZ)-$$-${PEER}"
OUT="$DIR/$SESSION.out"
TIMING="$DIR/$SESSION.timing"

# --flush : sans lui, script n'écrit son journal que par blocs de 4 Ko. La
# transcription retarde alors sur la session, et un conteneur détruit
# brutalement emporte le bloc non vidé -- c'est-à-dire l'activité la plus
# récente, précisément celle qui compte.
#
# --output-limit : la transcription écrit sur le disque du worker ce que le
# joueur voit passer. Sans borne, un « yes » suffirait à saturer la couche
# inscriptible du conteneur. 32 Mo est hors d'atteinte d'une session normale
# (quelques kilooctets) ; les atteindre relève de l'abus.
if [ -n "$CMD" ]; then
    exec script --quiet --return --flush --output-limit 32M \
        --log-out "$OUT" --log-timing "$TIMING" \
        --command "$CMD"
else
    exec script --quiet --return --flush --output-limit 32M \
        --log-out "$OUT" --log-timing "$TIMING"
fi

fallback
