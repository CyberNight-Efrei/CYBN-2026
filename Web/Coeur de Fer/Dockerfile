FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FLAG=CYBN{r0b0t_l0v3_x0r3d_h34rt}

WORKDIR /app

COPY src/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ /app/

EXPOSE 5000

CMD exec gunicorn --bind 0.0.0.0:5000 \
      --workers 2 --threads 4 --worker-class gthread \
      --timeout 30 --graceful-timeout 20 \
      --max-requests 800 --max-requests-jitter 100 \
      app:app
