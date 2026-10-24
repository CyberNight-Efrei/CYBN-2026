#!/bin/bash
set -e


if [ -z "${APP_FTP_PASSWORD:-}" ]; then
    echo "Erreur : APP_FTP_PASSWORD doit être défini."
    exit 1
fi
if [ -z "${USER:-}" ]; then
    echo "Erreur : USER doit être défini."
    exit 1
fi

# Définir le mot de passe du compte FTP
echo "${USER}:${APP_FTP_PASSWORD}" | chpasswd
echo "root:rootP@ssword!!1998" | chpasswd

# Autoriser uniquement app pour FTP
echo "${USER}" > /etc/vsftpd.userlist
chmod 600 /etc/vsftpd.userlist

# Vérifier la configuration SSH
/usr/sbin/sshd -t

# Lancer SSH en arrière-plan
/usr/sbin/sshd

# Maintenir le serveur FTP au premier plan
exec /usr/sbin/vsftpd /etc/vsftpd.conf