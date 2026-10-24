FROM python:3.12-slim

WORKDIR /app
COPY src/server.py .

RUN useradd --uid 10001 --create-home chall
USER chall

EXPOSE 1337
CMD ["python", "-u", "server.py"]
