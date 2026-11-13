FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ ./src/

ENV FLAG="CYBN{l34ky_gr4phql_r3s0lv3r}" \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

EXPOSE 5000
CMD ["python", "src/app.py"]
