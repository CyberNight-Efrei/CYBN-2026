FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends lua5.4 socat \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m ctf

COPY src/server.lua src/run.sh /app/
COPY flag.txt /app/flag.txt

RUN chown -R root:root /app && chmod -R a=rX /app && chmod 0555 /app/run.sh

USER ctf
WORKDIR /app
EXPOSE 8080
CMD ["socat", "TCP-LISTEN:8080,reuseaddr,fork", "EXEC:/app/run.sh"]
