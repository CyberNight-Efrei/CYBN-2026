FROM debian:latest

ENV DEBIAN_FRONTEND=noninteractive
ENV USER=alicia
ENV PASSWORD=miracle

USER root

# Aucun client curl n'est installé : l'initialisation de la file utilise Pika/AMQP.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        rabbitmq-server \
        openssh-server \
        python3-pika \
        tcpdump && \
    rm -rf /var/lib/apt/lists/*

# Conserver l'API Management pour l'accès par tunnel SSH depuis le client.
RUN rabbitmq-plugins enable --offline rabbitmq_management

# Supprimer rabbitmqadmin : il n'est pas nécessaire au serveur.
RUN find /usr /opt -name rabbitmqadmin \
    \( -type f -o -type l \) -delete 2>/dev/null || true

# Réserver les outils d'administration RabbitMQ à root.
# rabbitmqctl est conservé car entrypoint.sh l'utilise.
RUN for cmd in \
        rabbitmqctl \
        rabbitmq-diagnostics \
        rabbitmq-plugins \
        rabbitmq-queues \
        rabbitmq-upgrade \
        rabbitmq-reset \
        rabbitmq-service \
        rabbitmq-streams \
        python \
        python2 \
        python2.7 \
        python3 \
        python3.*; do \
        path="$(command -v "$cmd" 2>/dev/null || true)"; \
        if [ -n "$path" ]; then \
            chown root:rabbitmq "$path"; \
            chmod 750 "$path"; \
        fi; \
    done

# Garantir que le serveur RabbitMQ reste exécutable par root
RUN chmod 755 "$(command -v rabbitmq-server)"


RUN for cmd in \
        pip pip3 \
        ipython ipython3 \
        pydoc pydoc3; do \
        path="$(command -v "$cmd" 2>/dev/null || true)"; \
        if [ -n "$path" ]; then \
            chown root:root "$path"; \
            chmod 700 "$path"; \
        fi; \
    done

# RabbitMQ : AMQP et API HTTP de gestion accessibles uniquement en loopback.
RUN printf "%s\n" \
    "listeners.tcp.default = 127.0.0.1:5672" \
    "management.tcp.ip = 127.0.0.1" \
    "management.tcp.port = 15672" \
    "loopback_users.guest = true" \
    > /etc/rabbitmq/rabbitmq.conf

# Compte SSH du challenge.
RUN useradd --create-home --shell /bin/bash "$USER" && \
    passwd -l "$USER" && \
    mkdir -p /run/sshd

# SSH : autoriser les tunnels locaux uniquement vers AMQP et l'API Management.
RUN printf "%s\n" \
    "PermitRootLogin no" \
    "PasswordAuthentication yes" \
    "KbdInteractiveAuthentication no" \
    "AllowUsers ${USER}" \
    "AllowTcpForwarding local" \
    "PermitOpen 127.0.0.1:5672 127.0.0.1:15672 localhost:5672 localhost:15672" \
    "X11Forwarding no" \
    "LogLevel VERBOSE" \
    "ForceCommand /usr/local/bin/cybn-record" \
    >> /etc/ssh/sshd_config

# ForceCommand enregistre chaque session SSH ; la transcription part par la
# sortie standard du conteneur (voir entrypoint.sh). Le trafic tunnelisé
# (direct-tcpip) n'atteint jamais un shell et reste donc invisible ici : angle
# mort connu et accepté.
COPY cybn-record.sh /usr/local/bin/cybn-record
RUN chmod 555 /usr/local/bin/cybn-record && \
    mkdir -p /var/log/cybn && chmod 1733 /var/log/cybn

RUN printf "CYBN{Th3_Wh1te_R4Bb17_i5_CréT1n}" > /root/flag.txt && \
    chmod 440 /root/flag.txt

COPY queue.py /queue.py
RUN chown root:rabbitmq /queue.py && chmod 440 /queue.py

COPY entrypoint.sh /entrypoint.sh
RUN chmod 500 /entrypoint.sh

EXPOSE 22
CMD ["/entrypoint.sh"]
