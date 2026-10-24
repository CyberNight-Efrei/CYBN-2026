FROM alpine:3.22

RUN apk add --no-cache bash openssh-server shadow

RUN adduser -D -u 1000 \
    -h /home/builtin \
    -s /bin/bash builtin \
    && echo 'builtin:builtin' | chpasswd

RUN printf '%s\n' \
    'Port 22' \
    'PermitRootLogin no' \
    'PasswordAuthentication yes' \
    'PubkeyAuthentication no' \
    'KbdInteractiveAuthentication no' \
    'AllowUsers builtin' \
    'PermitTTY yes' \
    'DisableForwarding yes' \
    'PermitUserEnvironment no' \
    'PermitUserRC no' \
    'MaxAuthTries 3' \
    'MaxSessions 2' \
    'Subsystem sftp internal-sftp' \
    > /etc/ssh/sshd_config

RUN ssh-keygen -A && mkdir -p /run/sshd

ARG FLAG=CYBN{BASH_BUILTINS_POWER!!!}

RUN RANDOM_DIR=$(od -An -N16 -tx1 /dev/urandom | tr -d ' \n') \
    && mkdir -p "/home/builtin/$RANDOM_DIR" \
    && mkdir -p "/home/builtin/$RANDOM_DIR flag_dir" \
    && printf '%s\n' \
       "# Bien joué, tu peux valider avec le flag suivant : $FLAG" \
       > "/home/builtin/$RANDOM_DIR flag_dir/.passwd" \
    && chown -R root:root /home/builtin \
    && chmod 755 /home/builtin \
    && chmod 755 "/home/builtin/$RANDOM_DIR" \
    && chmod 755 "/home/builtin/$RANDOM_DIR flag_dir" \
    && chmod 444 "/home/builtin/$RANDOM_DIR flag_dir/.passwd"

# Retire l'exécution de tous les binaires sauf bash
RUN find /bin /sbin /usr/bin /usr/sbin \
    -type f -perm /111 \
    ! -name bash \
    -exec chmod 700 {} + \
    && chmod 755 /bin/bash

RUN printf '%s\n' \
    'set disable-completion on' \
    'set show-all-if-ambiguous off' \
    > /etc/inputrc

RUN printf '%s\n' \
    'export PATH=/nonexistent' \
    'export HISTFILE=/dev/null' \
    'export PS1="\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w \$\[\033[00m\] "' \
    'export INPUTRC=/etc/inputrc' \
    'set +o emacs' \
    'set +o vi' \
    'cd /home/builtin' \
    > /etc/profile \
    && cp /etc/profile /home/builtin/.bash_profile \
    && cp /etc/profile /home/builtin/.bashrc \
    && chown root:root \
       /etc/profile \
       /etc/inputrc \
       /home/builtin/.bash_profile \
       /home/builtin/.bashrc \
    && chmod 644 \
       /etc/profile \
       /etc/inputrc \
       /home/builtin/.bash_profile \
       /home/builtin/.bashrc

RUN printf '%s\n' \
    '========================================' \
    '         BASH BUILTINS CHALLENGE' \
    '========================================' \
    '' \
    'Bienvenue dans ce challenge !' \
    '' \
    'Les commandes externes sont indisponibles.' \
    'Seules les fonctionnalites de Bash' \
    'vous permettront de retrouver le flag.' \
    '' \
    'Bonne chance !' \
    '========================================' \
    > /etc/motd

ENV PATH=/nonexistent
ENV INPUTRC=/etc/inputrc
ENV HISTFILE=/dev/null

EXPOSE 22
CMD ["/usr/sbin/sshd", "-D", "-e"]
