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
    >> /etc/ssh/sshd_config

RUN printf "CYBN{Th3_Wh1te_R4Bb17_i5_CréT1n}" > /root/flag.txt && \
    chmod 440 /root/flag.txt

COPY queue.py /queue.py
RUN chown root:rabbitmq /queue.py && chmod 440 /queue.py

COPY entrypoint.sh /entrypoint.sh
RUN chmod 500 /entrypoint.sh

EXPOSE 22
CMD ["/entrypoint.sh"]
