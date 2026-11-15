FROM python:3.11-slim AS model
ARG MODEL_ID=Salesforce/blip-image-captioning-base
ARG MODEL_REVISION=cab088ce3bed7a6b7ead5bf9bcd1ce3d4c69ee78
RUN pip install --no-cache-dir huggingface-hub==0.26.5
RUN python -c "from huggingface_hub import snapshot_download; snapshot_download(repo_id='${MODEL_ID}', revision='${MODEL_REVISION}', local_dir='/models/blip', allow_patterns=['*.json','*.txt','pytorch_model.bin'])"

FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 MODEL_PATH=/models/blip \
    CATALOG_PATH=/app/catalog/cards.json REFERENCE_DIR=/app/references
WORKDIR /app
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch==2.5.1
COPY src/ml-service/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY --from=model /models/blip /models/blip
COPY src/ml-service/app.py ./app.py
COPY src/ml-service/jobs.py ./jobs.py
COPY src/ml-service/storage.py ./storage.py
COPY src/server/data/cards.json ./catalog/cards.json
COPY src/client/public/creatures ./references
RUN useradd --system --uid 10001 --create-home scanner && mkdir -p /data/images /data/logs && chown -R scanner:scanner /app /data
USER scanner
EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--no-access-log"]
