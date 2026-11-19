import asyncio
import io
import json
import os
import re
import secrets
from contextlib import asynccontextmanager
from pathlib import Path

import torch
import torch.nn.functional as functional
from fastapi import Depends, FastAPI, HTTPException, Request
from PIL import Image, UnidentifiedImageError
from transformers import BlipForConditionalGeneration, BlipProcessor, StoppingCriteria, StoppingCriteriaList
from jobs import JobQueue
from storage import configure_logging, logger

MODEL_ID = os.getenv("MODEL_ID", "Salesforce/blip-image-captioning-base")
MODEL_REVISION = os.getenv(
    "MODEL_REVISION", "cab088ce3bed7a6b7ead5bf9bcd1ce3d4c69ee78"
)
MODEL_PATH = os.getenv("MODEL_PATH", "/models/blip")
SERVICE_TOKEN = os.getenv("ML_SERVICE_TOKEN", "local-ml-token")
MATCH_THRESHOLD = float(os.getenv("MATCH_THRESHOLD", "0.96"))
MAX_IMAGE_BYTES = 2 * 1024 * 1024
MAX_IMAGE_PIXELS = 16_000_000
CATALOG_PATH = Path(os.getenv("CATALOG_PATH", "/app/catalog/cards.json"))
REFERENCE_DIR = Path(os.getenv("REFERENCE_DIR", "/app/references"))
STORAGE_DIR = Path(os.getenv("ML_STORAGE_DIR", "/data"))
DEVICE_NAME = os.getenv("ML_DEVICE", "cpu").lower()
if DEVICE_NAME not in {"cpu", "cuda", "auto"}:
    raise RuntimeError("ML_DEVICE must be cpu, cuda or auto.")
if DEVICE_NAME == "auto":
    DEVICE_NAME = "cuda" if torch.cuda.is_available() else "cpu"
if DEVICE_NAME == "cuda" and not torch.cuda.is_available():
    raise RuntimeError("CUDA requested but unavailable: check the PyTorch image and Docker GPU access.")
DEVICE = torch.device(DEVICE_NAME)
REFERENCE_BATCH_SIZE = int(os.getenv("REFERENCE_BATCH_SIZE", "1" if DEVICE_NAME == "cuda" else "40"))
if REFERENCE_BATCH_SIZE < 1:
    raise RuntimeError("REFERENCE_BATCH_SIZE must be positive.")
torch.backends.cuda.matmul.allow_tf32 = False
torch.backends.cudnn.allow_tf32 = False

torch.set_num_threads(max(1, int(os.getenv("TORCH_THREADS", "4"))))
Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS

processor = None
model = None
catalog = []
reference_embeddings = None
reference_hashes = []


def difference_hash(image: Image.Image) -> int:
    pixels = list(image.convert("L").resize((9, 8), Image.Resampling.LANCZOS).getdata())
    value = 0
    for row in range(8):
        for column in range(8):
            left = pixels[row * 9 + column]
            right = pixels[row * 9 + column + 1]
            value = (value << 1) | int(left > right)
    return value


def open_image(raw: bytes) -> Image.Image:
    try:
        image = Image.open(io.BytesIO(raw))
        image.load()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as error:
        raise HTTPException(400, "Invalid or unsafe image.") from error
    if image.width < 16 or image.height < 16:
        raise HTTPException(400, "The illustration is too small.")
    if image.width > 4096 or image.height > 4096:
        raise HTTPException(400, "The illustration dimensions are too large.")
    if image.width * image.height > MAX_IMAGE_PIXELS:
        raise HTTPException(400, "The illustration contains too many pixels.")
    return image.convert("RGB")


def vision_embedding(images):
    values = processor(images=images, return_tensors="pt").pixel_values.to(DEVICE)
    with torch.inference_mode():
        hidden = model.vision_model(pixel_values=values).last_hidden_state[:, 0, :]
    return functional.normalize(hidden.float(), dim=-1)


def load_runtime():
    global processor, model, catalog, reference_embeddings, reference_hashes
    processor = BlipProcessor.from_pretrained(MODEL_PATH, local_files_only=True)
    model = BlipForConditionalGeneration.from_pretrained(
        MODEL_PATH, local_files_only=True
    )
    model.to(DEVICE)
    model.eval()
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf8"))
    images = []
    for card in catalog:
        filename = Path(card["image"]).name
        image = Image.open(REFERENCE_DIR / filename).convert("RGB")
        images.append(image)
        reference_hashes.append(difference_hash(image))
    reference_embeddings = torch.cat([
        vision_embedding(images[index:index + REFERENCE_BATCH_SIZE])
        for index in range(0, len(images), REFERENCE_BATCH_SIZE)
    ])


class GenerationProgress(StoppingCriteria):
    def __init__(self, report):
        self.report = report
        self.step = 0

    def __call__(self, input_ids, scores, **kwargs):
        self.step = min(24, self.step + 1)
        self.report("generating", 20 + self.step * 65 / 24, self.step)
        # Observe generation only: never change beam selection or stop a valid job.
        return torch.zeros(input_ids.shape[0], dtype=torch.bool, device=input_ids.device)


def analyse(raw, report):
    report("encoding", 8)
    image = open_image(raw)
    values = processor(images=image, return_tensors="pt").pixel_values.to(DEVICE)
    with torch.inference_mode():
        generated = model.generate(
            pixel_values=values,
            num_beams=3,
            max_new_tokens=24,
            do_sample=False,
            stopping_criteria=StoppingCriteriaList([GenerationProgress(report)]),
        )
        report("matching", 90)
        candidate = model.vision_model(pixel_values=values).last_hidden_state[:, 0, :]
    caption = processor.decode(generated[0], skip_special_tokens=True).strip()

    candidate_hash = difference_hash(image)
    distances = [(candidate_hash ^ value).bit_count() for value in reference_hashes]
    closest_hash = min(range(len(distances)), key=distances.__getitem__)
    if distances[closest_hash] <= 4:
        return {"caption": caption, "match": {
            "slug": catalog[closest_hash]["slug"],
            "score": 1.0 - distances[closest_hash] / 64.0,
        }}

    candidate = functional.normalize(candidate.float(), dim=-1)
    similarities = torch.matmul(reference_embeddings, candidate.T).squeeze(1)
    score, index = similarities.max(dim=0)
    if score.item() >= MATCH_THRESHOLD:
        return {"caption": caption, "match": {"slug": catalog[index.item()]["slug"], "score": score.item()}}
    return {"caption": caption, "match": None}


queue = JobQueue(analyse, archive_dir=STORAGE_DIR / "images")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    configure_logging(STORAGE_DIR / "logs")
    logger.info("event=starting model=%s revision=%s device=%s dtype=float32 threads=%s archive=%s", MODEL_ID, MODEL_REVISION, DEVICE_NAME, torch.get_num_threads(), queue.archive_dir)
    await asyncio.to_thread(load_runtime)
    logger.info("event=ready references=%d max_pending=%d job_timeout_s=%d", len(catalog), queue.max_pending, queue.timeout)
    queue.start()
    try:
        yield
    finally:
        await queue.close()
        logger.info("event=stopped")


app = FastAPI(title="Scanner d’illustrations Cybermon", lifespan=lifespan)


@app.get("/health")
def health():
    return {
        "ok": model is not None,
        "model": MODEL_ID,
        "revision": MODEL_REVISION,
        "references": len(catalog),
        "jobApiVersion": 1,
        "device": DEVICE_NAME,
        "deviceName": torch.cuda.get_device_name(DEVICE) if DEVICE_NAME == "cuda" else "CPU",
        "dtype": "float32",
        "generation": {"numBeams": 3, "maxNewTokens": 24, "doSample": False},
    }


def authorize(request: Request):
    authorization = request.headers.get("authorization", "")
    expected = f"Bearer {SERVICE_TOKEN}"
    if not secrets.compare_digest(authorization, expected):
        logger.warning("event=request_rejected reason=unauthorized")
        raise HTTPException(401, "Invalid service token.")


async def read_illustration(request):
    if request.headers.get("content-type") not in {
        "image/png",
        "image/jpeg",
        "image/webp",
    }:
        raise HTTPException(415, "Unsupported image type.")
    raw = bytearray()
    async for chunk in request.stream():
        raw.extend(chunk)
        if len(raw) > MAX_IMAGE_BYTES:
            raise HTTPException(413, "Image is too large.")
    if not raw:
        raise HTTPException(413, "Image is empty or too large.")
    image = await asyncio.to_thread(open_image, raw)
    session = request.headers.get("X-Scanner-Session", "direct")
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", session):
        session = "direct"
    metadata = {
        "session": session, "mimeType": request.headers["content-type"],
        "width": image.width, "height": image.height,
        "model": MODEL_ID, "revision": MODEL_REVISION,
        "device": DEVICE_NAME, "dtype": "float32",
    }
    return bytes(raw), metadata


@app.post("/jobs", status_code=202, dependencies=[Depends(authorize)])
async def submit_job(request: Request):
    raw, metadata = await read_illustration(request)
    try:
        key = queue.submit(raw, metadata)
    except OverflowError as error:
        logger.warning("event=request_rejected session=%s reason=queue_full bytes=%d", metadata["session"], len(raw))
        raise HTTPException(429, str(error)) from error
    except OSError as error:
        logger.exception("event=archive_failed session=%s bytes=%d", metadata["session"], len(raw))
        raise HTTPException(503, "Le scanner ne peut pas enregistrer l'illustration.") from error
    return queue.get(key)


@app.get("/jobs/{key}", dependencies=[Depends(authorize)])
async def job_status(key: str):
    status = queue.get(key)
    if not status:
        raise HTTPException(404, "Analyse introuvable ou expirée.")
    return status


@app.delete("/jobs/{key}", dependencies=[Depends(authorize)])
async def cancel_job(key: str):
    status = queue.cancel(key)
    if not status:
        raise HTTPException(404, "Analyse introuvable ou expirée.")
    return status


@app.post("/caption", dependencies=[Depends(authorize)])
async def caption(request: Request):
    # Compatibility for instances still using the synchronous endpoint.
    status = await submit_job(request)
    await queue.jobs[status["id"]]["done"].wait()
    status = queue.get(status["id"])
    if status["status"] != "done":
        raise HTTPException(503, status["error"])
    return status["result"]
