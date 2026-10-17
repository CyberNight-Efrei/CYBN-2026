FROM debian:bookworm-slim AS build

RUN apt-get update && apt-get install -y --no-install-recommends gcc libc6-dev \
    && rm -rf /var/lib/apt/lists/*

COPY src/server.c /tmp/server.c

RUN gcc -fno-stack-protector -O0 -o /tmp/server /tmp/server.c


FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends socat git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m ctf

COPY web/ /app/web/

COPY flag.txt /app/flag.txt

COPY --from=build /tmp/server /app/web/server

RUN cp /lib/x86_64-linux-gnu/libc.so.6 /app/web/libc.so.6 \
    && chmod +x /app/web/server \
    && cd /app/web \
    && git init -q \
    && git config user.email "dev@bocchi.local" \
    && git config user.name "bocchi" \
    && git config gc.auto 0 \
    && git add CLAUDE.md server libc.so.6 \
    && git commit -qm "ship: patch binaire a la volee (cf CLAUDE.md), source pas versionnee"

RUN chown -R root:root /app \
    && chmod -R a=rX /app \
    && chmod 0555 /app/web/server

USER ctf
WORKDIR /app/web
EXPOSE 8080
CMD ["socat", "TCP-LISTEN:8080,reuseaddr,fork", "EXEC:./server"]
