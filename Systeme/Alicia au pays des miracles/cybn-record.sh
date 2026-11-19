#!/bin/sh
# CyberNight session recorder, run by sshd's ForceCommand for every session.
#
# Records the terminal session with script(1) into /var/log/cybn. The shipper
# started by entrypoint.sh streams those files to the container's stdout, where
# the Docker log driver carries them off the worker as they are written. A
# player who later gains root can stop the stream, but cannot retract what has
# already left the box.
#
# THE ONE RULE: this must never prevent a login. Every failure path falls
# through to a plain shell. A missing transcript is a gap in the evidence; a
# recorder that aborts is a challenge nobody can solve. An earlier revision
# dereferenced an unset SSH_ORIGINAL_COMMAND under `set -u` and dash exited
# before reaching exec -- the player got no shell at all. Hence: every expansion
# of an sshd-supplied variable carries a default, and the fallback is a function
# called from every branch rather than a line at the bottom that control flow
# can miss.
#
# Not recorded: port forwarding. A direct-tcpip channel never reaches a shell,
# so tunnelled bytes are invisible here by construction. sshd's LogLevel VERBOSE
# records that a forward was opened and to where, which is the trace that
# remains. Known and accepted blind spot.

set -u

DIR=/var/log/cybn
SHELL_BIN="${SHELL:-/bin/bash}"
CMD="${SSH_ORIGINAL_COMMAND:-}"

# Start the session unrecorded. Used wherever recording cannot be set up.
fallback() {
    if [ -n "$CMD" ]; then
        exec "$SHELL_BIN" -c "$CMD"
    fi
    exec "$SHELL_BIN"
}

command -v script >/dev/null 2>&1 || fallback
mkdir -p "$DIR" 2>/dev/null
[ -w "$DIR" ] || fallback

# Session id: time, pid, and the client address sshd hands us. Enough to tell
# two concurrent logins apart and to line a transcript up against the pcap.
PEER="$(printf '%s' "${SSH_CONNECTION:-unknown}" | tr -c 'A-Za-z0-9.:' '_')"
SESSION="$(date -u +%Y%m%dT%H%M%SZ)-$$-${PEER}"
OUT="$DIR/$SESSION.out"
TIMING="$DIR/$SESSION.timing"

# --log-out plus --log-timing is the pair asciinema replay is built from.
# --return passes the shell's exit status through, so the player sees the same
# code they would without us. --quiet keeps script's banner off their terminal.
if [ -n "$CMD" ]; then
    exec script --quiet --return \
        --log-out "$OUT" --log-timing "$TIMING" \
        --command "$CMD"
else
    exec script --quiet --return \
        --log-out "$OUT" --log-timing "$TIMING"
fi

# Only reached if exec itself failed.
fallback
