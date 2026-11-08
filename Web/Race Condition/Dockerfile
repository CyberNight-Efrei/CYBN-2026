
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    CHALLENGE_FLAG=CYBN{R4c3_C0nd1T10n_V1P_4cc3ss} \
    FLASK_SECRET_KEY=5f5d6cfd77a36e3fc898ab31236d98e9115a35596cdb6a42163c7333fbddc4dc

WORKDIR /app

COPY src/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ /app/

EXPOSE 8080

CMD ["python", "app.py"]
