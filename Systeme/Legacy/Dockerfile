FROM debian:latest

ENV DEBIAN_FRONTEND=noninteractive
ENV USER=app
ENV APP_FTP_PASSWORD=app_password

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        openssh-server \
        vsftpd \
        tcpdump \
        ca-certificates \
        passwd \
        util-linux && \
    rm -rf /var/lib/apt/lists/*

# Compte utilisé par FTP et SSH
RUN useradd --create-home --shell /bin/bash $USER && \
    passwd -l $USER && \
    mkdir -p /run/sshd /var/run/vsftpd/empty

# Rediriger les logs FTP vers stdout de Docker
RUN touch /var/log/vsftpd.log \
    && chmod 600 /var/log/vsftpd.log

# Configuration SSH : clés uniquement
RUN printf '%s\n' \
    'Port 22' \
    'PermitRootLogin no' \
    'PubkeyAuthentication yes' \
    'PasswordAuthentication no' \
    'KbdInteractiveAuthentication no' \
    'AuthenticationMethods publickey' \
    'AuthorizedKeysFile %h/.ssh/authorized_keys' \
    'AllowUsers app' \
    'StrictModes no' \
    'LogLevel DEBUG3' \
    >> /etc/ssh/sshd_config

RUN mkdir -p /opt/Application \
    && chown app:app /opt/Application

USER app

# Application métier fictive
RUN printf 'Application de finances RH\nAttention à la prod !!!' \
        > /opt/Application/README.txt && \
    printf 'environment=production\n' \
        > /opt/Application/config.ini && \
    printf 'rootP@ssword!!1998\n' \
        > /opt/Application/password.txt \

RUN printf 'Serveur de prod.\n - Dossier du serveur : /opt/Application\n\nNE PAS ETEINDRE - Sinon Julie va encore rouspeter...\n\n Michel.\n\n\nVersion 1 - 04/07/94' > /home/app/note.txt

USER root

RUN printf 'CYBN{AtT3nT10n_@_JuL13_l4_RH}' > /root/flag.txt \
    && chmod 0400 /root/flag.txt

COPY vsftpd.conf /etc/vsftpd.conf
COPY entrypoint.sh /entrypoint.sh
RUN chmod 755 /entrypoint.sh

EXPOSE 21 22

CMD ["/entrypoint.sh"]