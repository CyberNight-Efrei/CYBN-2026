FROM debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive \
    USER=app \
    PYTHONUNBUFFERED=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3 \
        openssh-server \
        tcpdump \
        ca-certificates \
        passwd \
        util-linux && \
    rm -rf /var/lib/apt/lists/*

# Compte commun au serveur web et au service SSH.
RUN useradd --create-home --home-dir /home/app --shell /bin/bash app && \
    mkdir -p /run/sshd

# Configuration SSH : shell classique, clé publique uniquement, compte app seulement.
# StrictModes no et les permissions permissives de .ssh sont volontaires pour ce CTF.
RUN printf '%s\n' \
    'Port 22' \
    'AddressFamily any' \
    'ListenAddress 0.0.0.0' \
    'PermitRootLogin no' \
    'PubkeyAuthentication yes' \
    'PasswordAuthentication no' \
    'KbdInteractiveAuthentication no' \
    'AuthenticationMethods publickey' \
    'AuthorizedKeysFile /home/app/.ssh/authorized_keys' \
    'AllowUsers app' \
    'StrictModes no' \
    'UsePAM no' \
    'PermitEmptyPasswords no' \
    'PermitUserEnvironment no' \
    'AllowAgentForwarding no' \
    'AllowTcpForwarding no' \
    'X11Forwarding no' \
    'PermitTunnel no' \
    'PermitTTY yes' \
    'PrintMotd no' \
    'PrintLastLog yes' \
    'UseDNS no' \
    'LogLevel VERBOSE' \
    'PidFile /run/sshd.pid' \
    > /etc/ssh/sshd_config

# Fichiers métier conservés depuis la v1 : ils font partie du décor/scénario.
RUN mkdir -p /opt/Application && chown app:app /opt/Application
RUN mkdir -p /home/app/.ssh && chown app:app /home/app/.ssh

USER app
RUN printf 'Application de finances RH\nAttention à la prod !!!\n' > /opt/Application/README.txt && \
    printf 'environment=production\n' > /opt/Application/config.ini && \
    printf 'rootP@ssword!!1998\n' > /opt/Application/password.txt && \
    printf 'Serveur de prod.\n - Dossier du serveur : /opt/Application\n\nNE PAS ETEINDRE - Sinon Julie va encore rouspeter...\n\n Michel.\n\n\nVersion 2 - 04/07/94\n' > /home/app/note.txt && \
    printf 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCTx4XKb4SPGZG/eYL5OddbXERokAjhEXHLGfOwpabPGrDtJJC4Sqjk/bNGyy6y+UXP11WAN7zrQL/VkgzUQT8hyAxEixcpRX5fCBeKs9audWZgOM/Hi3eA64JTo+06M492tvsl2xi8UhtM2GjeTDsYZadOP53TSie083GX4yLAz0AZmC6/VDIIX5SnEhlL05T/tNicgGPOP0NCAReQ+mCBWJJmEJinflsHK1NCj+Iw1gAMmMPuo7YcSGpiTl8wzDQ6SF0vwqU44QCPOtghGTtzbz5yImUyd9M4iSjMgkVNuybE2kpF+Dk9pDwBaztCZg71jSWg4MtXeEkcQzGBTadr' > /home/app/.ssh/authorized_keys

USER root
RUN printf 'CYBN{AtT3nT10n_@_Jul13_l4_RH}' > /root/flag.txt && \
    chmod 0400 /root/flag.txt

COPY app.py /home/app/app.py
COPY entrypoint.sh /entrypoint.sh
RUN chown app:app /home/app/app.py && \
    chmod 0444 /home/app/app.py && \
    chmod 0755 /entrypoint.sh

EXPOSE 8080 22
CMD ["/entrypoint.sh"]
