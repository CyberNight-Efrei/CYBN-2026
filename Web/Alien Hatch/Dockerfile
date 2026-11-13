FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FLAG1=CYBN{z0rglub_r0t_c0sm1qu3} \
    FLAG2=CYBN{f1ltr3_anti_bav3_c0ntourn3} \
    FLAG3=CYBN{bl1nd_zorglub_sil3nci3ux}

WORKDIR /app

COPY src/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ /app/

EXPOSE 5000

CMD python -c "import app; app.init_db()" && \
    exec gunicorn --bind 0.0.0.0:5000 \
      --workers 2 --threads 4 --worker-class gthread \
      --timeout 30 --graceful-timeout 20 \
      --max-requests 800 --max-requests-jitter 100 \
      app:app
