FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
      nasm binutils python3 python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --break-system-packages \
      fastapi==0.115.6 uvicorn==0.34.0

RUN useradd -m -u 1000 ctf

RUN mkdir -p /srv/jail/ticketbox
COPY flag.txt /srv/jail/ticketbox/free_ticket_for_totoro_friend.txt

COPY src/ /app/
WORKDIR /app

RUN chown -R root:root /srv/jail /app \
    && chmod -R a=rX /srv/jail \
    && chmod -R a=rX /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TMPDIR=/sandbox

USER ctf
EXPOSE 8080
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
