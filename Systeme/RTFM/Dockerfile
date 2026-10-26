FROM debian:trixie-slim AS builder

ARG FLAG="CYBN{m4n_p4g3s_4r3_y0ur_b3st_fr13nds}"
ARG PASSWORD="gf_r34d_th3_s0urc3_n0t_th3_r3nd3r"

RUN apt-get update \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        vim gcc libc6-dev python3 binutils \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY src/ src/
COPY man/ man/

RUN python3 src/gen_secret.py "$PASSWORD" "$FLAG" > src/secret.h \
 && gcc -O2 -fPIC -fvisibility=hidden -Wall -Wextra -Isrc \
        -shared -Wl,-soname,libgetflag.so.1 \
        -o libgetflag.so.1.0 src/get_flag.c \
 && strip --strip-unneeded libgetflag.so.1.0

RUN sed -i "s|@PASSWORD@|$PASSWORD|" man/getflag.conf.5 \
 && grep -q "$PASSWORD" man/getflag.conf.5 \
 && gzip -9n man/*.[0-9]

FROM debian:trixie-slim

ENV LANG=C.UTF-8

RUN grep -rl 'path-exclude' /etc/dpkg/dpkg.cfg.d/ | xargs -r rm -f \
 && apt-get update \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        man-db manpages manpages-dev less groff-base \
        gcc libc6-dev \
        openssh-server \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends --reinstall \
        coreutils gzip grep findutils sed \
 && rm -rf /var/lib/apt/lists/*

COPY --from=builder /build/libgetflag.so.1.0 /usr/local/lib/
COPY src/get_flag.h /usr/local/include/
RUN ln -s libgetflag.so.1.0 /usr/local/lib/libgetflag.so.1 \
 && ln -s libgetflag.so.1   /usr/local/lib/libgetflag.so \
 && chmod 644 /usr/local/lib/libgetflag.so.1.0 /usr/local/include/get_flag.h \
 && ldconfig
COPY --from=builder /build/man/get_flag.1.gz      /usr/local/share/man/man1/
COPY --from=builder /build/man/get_flag.3.gz      /usr/local/share/man/man3/
COPY --from=builder /build/man/getflag.conf.5.gz  /usr/local/share/man/man5/
COPY --from=builder /build/man/get_flag.7.gz      /usr/local/share/man/man7/
RUN chmod 644 /usr/local/share/man/man*/*.gz \
 && mandb -q

RUN export MANPAGER=cat \
 && man get_flag      | grep -q "ceci n'est pas une commande" \
 && man 3 get_flag    | grep -q "CHANGEME" \
 && man -k get_flag   | grep -q "get_flag (7)" \
 && man -K -s 5 -w gf_ | grep -q "getflag.conf.5" \
 && ! man 5 getflag.conf | grep -q "gf_" \
 && man -w zcat >/dev/null \
 && echo "[ok] man pages fonctionnelles"

RUN useradd -m -s /bin/bash cybn \
 && echo 'cybn:cybn' | chpasswd

RUN printf '%s\n' \
        'PasswordAuthentication yes' \
        'KbdInteractiveAuthentication no' \
        'PermitRootLogin no' \
        'AllowUsers cybn' \
        'PrintMotd no' \
        'X11Forwarding no' \
        'AllowTcpForwarding no' \
        'AllowAgentForwarding no' \
        'PermitTunnel no' \
        > /etc/ssh/sshd_config.d/ctf.conf \
 && rm -f /etc/update-motd.d/* \
 && : > /etc/motd \

EXPOSE 22
CMD ["/usr/sbin/sshd", "-D", "-e"]
