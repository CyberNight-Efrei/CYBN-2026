FROM debian:latest

ENV DEBIAN_FRONTEND=noninteractive
ENV USER=alicia
ENV PASSWORD=miracle

USER root

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        rabbitmq-server \
        openssh-server \
        curl \
        ca-certificates \
        tcpdump \
    rm -rf /var/lib/apt/lists/*

# Activer l"API HTTP de gestion, utilisée uniquement en interne
RUN rabbitmq-plugins enable --offline rabbitmq_management

# RabbitMQ : AMQP et API HTTP accessibles uniquement en loopback
RUN printf "%s\n" \
    "listeners.tcp.default = 127.0.0.1:5672" \
    "management.tcp.ip = 127.0.0.1" \
    "management.tcp.port = 15672" \
    "loopback_users.guest = true" \
    > /etc/rabbitmq/rabbitmq.conf

# Compte SSH du challenge
RUN useradd --create-home --shell /bin/bash $USER && \
    passwd -l $USER && \
    mkdir -p /run/sshd

# SSH : accès au tunnel uniquement vers RabbitMQ
RUN printf "%s\n" \
    "PermitRootLogin no" \
    "PasswordAuthentication yes" \
    "KbdInteractiveAuthentication no" \
    "AllowUsers ${USER}" \
    "AllowTcpForwarding local" \
    "PermitOpen 127.0.0.1:5672" \
    "X11Forwarding no" \
    >> /etc/ssh/sshd_config

# Initialisation du challenge et lancement des services
COPY entrypoint.sh /entrypoint.sh
RUN chmod 700 /entrypoint.sh

EXPOSE 22

CMD ["/entrypoint.sh"]