FROM python:3.14-slim

WORKDIR /challenge

RUN apt-get update \
    && apt-get -y --no-install-recommends install socat less \
    && rm -rf /var/lib/apt/lists/*

COPY ./src/challenge.py .
COPY ./src/requirements.txt .
COPY ./entrypoint.sh .

RUN python3 -m pip install --no-cache-dir -r requirements.txt \
	&& groupadd challenge \
    && useradd --no-create-home -d /challenge -g challenge challenge \
    && chown -R challenge:challenge /challenge/ \
    && chmod -R 755 /challenge/

ENV LISTEN_PORT=7000
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

RUN echo "CYBN{4_fr3sh_1nt3rpr3t3r_h4s_n0_4ud1t_h00ks}" > /flag

EXPOSE 7000
ENTRYPOINT ["./entrypoint.sh"]
