#!/bin/bash
set -Eeuo pipefail

if [[ "${USER:-app}" != "app" ]]; then
    echo "Erreur : le service est conçu pour fonctionner avec l'utilisateur app." >&2
    exit 1
fi

id app >/dev/null 2>&1 || { echo "Erreur : le compte app est absent." >&2; exit 1; }

# Conservation du mot de passe root historique : il fait partie du scénario CTF.
# SSH interdit néanmoins toute connexion directe en root.
echo 'root:rootP@ssword!!1998' | chpasswd

# Mot de passe local aléatoire, inconnu et non journalisé : le compte reste
# compatible avec l'authentification par clé, tandis que SSH interdit les mots de passe.
APP_RANDOM_PASSWORD="$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')"
printf 'app:%s\n' "$APP_RANDOM_PASSWORD" | chpasswd
unset APP_RANDOM_PASSWORD

install -d -o root -g root -m 0755 /run/sshd
install -d -o app -g app -m 0777 /home/app/.ssh

# Permissions volontairement permissives pour le challenge :
# StrictModes est désactivé dans sshd_config et authorized_keys est modifiable
# depuis le bloc-notes web, qui tourne lui aussi sous l'identité app.
if [[ -L /home/app/.ssh || -L /home/app/.ssh/authorized_keys ]]; then
    echo "Erreur : .ssh et authorized_keys ne doivent pas être des liens symboliques." >&2
    exit 1
fi
if [[ ! -e /home/app/.ssh/authorized_keys ]]; then
    install -o app -g app -m 0666 /dev/null /home/app/.ssh/authorized_keys
else
    chown app:app /home/app/.ssh/authorized_keys
    chmod 0666 /home/app/.ssh/authorized_keys
fi
chmod 0777 /home/app/.ssh

# Crée les clés d'hôte manquantes, puis valide la configuration SSH.
ssh-keygen -A
/usr/sbin/sshd -t

# SSH et le serveur web sont supervisés par ce script afin qu'un arrêt de l'un
# arrête proprement le conteneur.
/usr/sbin/sshd -D -e &
SSH_PID=$!
runuser --user app -- python3 -u /home/app/app.py &
WEB_PID=$!

cleanup() {
    kill "$WEB_PID" "$SSH_PID" 2>/dev/null || true
    wait "$WEB_PID" 2>/dev/null || true
    wait "$SSH_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

set +e
wait -n "$SSH_PID" "$WEB_PID"
STATUS=$?
set -e
exit "$STATUS"
