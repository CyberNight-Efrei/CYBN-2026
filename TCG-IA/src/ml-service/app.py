import asyncio
import io
import json
import os
import secrets
from contextlib import asynccontextmanager
from pathlib import Path

import torch
import torch.nn.functional as functional
from fastapi import FastAPI, HTTPException, Request
from PIL import Image, UnidentifiedImageError
from transformers import BlipForConditionalGeneration, BlipProcessor

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

torch.set_num_threads(max(1, int(os.getenv("TORCH_THREADS", "4"))))
Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS

processor = None
model = None
catalog = []
reference_embeddings = None
reference_hashes = []
inference_lock = asyncio.Semaphore(1)


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
    values = processor(images=images, return_tensors="pt").pixel_values
    with torch.inference_mode():
        hidden = model.vision_model(pixel_values=values).last_hidden_state[:, 0, :]
    return functional.normalize(hidden.float(), dim=-1)


def load_runtime():
    global processor, model, catalog, reference_embeddings, reference_hashes
    processor = BlipProcessor.from_pretrained(MODEL_PATH, local_files_only=True)
    model = BlipForConditionalGeneration.from_pretrained(
        MODEL_PATH, local_files_only=True
    )
    model.eval()
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf8"))
    images = []
    for card in catalog:
        filename = Path(card["image"]).name
        image = Image.open(REFERENCE_DIR / filename).convert("RGB")
        images.append(image)
        reference_hashes.append(difference_hash(image))
    reference_embeddings = vision_embedding(images)


def analyse(image: Image.Image):
    values = processor(images=image, return_tensors="pt").pixel_values
    with torch.inference_mode():
        generated = model.generate(
            pixel_values=values,
            num_beams=3,
            max_new_tokens=24,
            do_sample=False,
        )
        candidate = model.vision_model(pixel_values=values).last_hidden_state[:, 0, :]
    caption = processor.decode(generated[0], skip_special_tokens=True).strip()

    candidate_hash = difference_hash(image)
    distances = [(candidate_hash ^ value).bit_count() for value in reference_hashes]
    closest_hash = min(range(len(distances)), key=distances.__getitem__)
    if distances[closest_hash] <= 4:
        return caption, {
            "slug": catalog[closest_hash]["slug"],
            "score": 1.0 - distances[closest_hash] / 64.0,
        }

    candidate = functional.normalize(candidate.float(), dim=-1)
    similarities = torch.matmul(reference_embeddings, candidate.T).squeeze(1)
    score, index = similarities.max(dim=0)
    if score.item() >= MATCH_THRESHOLD:
        return caption, {"slug": catalog[index.item()]["slug"], "score": score.item()}
    return caption, None


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await asyncio.to_thread(load_runtime)
    yield


app = FastAPI(title="Scanner d’illustrations Cybermon", lifespan=lifespan)


@app.get("/health")
def health():
    return {
        "ok": model is not None,
        "model": MODEL_ID,
        "revision": MODEL_REVISION,
        "references": len(catalog),
    }


@app.post("/caption")
async def caption(request: Request):
    authorization = request.headers.get("authorization", "")
    expected = f"Bearer {SERVICE_TOKEN}"
    if not secrets.compare_digest(authorization, expected):
        raise HTTPException(401, "Invalid service token.")
    if request.headers.get("content-type") not in {
        "image/png",
        "image/jpeg",
        "image/webp",
    }:
        raise HTTPException(415, "Unsupported image type.")
    raw = await request.body()
    if not raw or len(raw) > MAX_IMAGE_BYTES:
        raise HTTPException(413, "Image is empty or too large.")
    image = open_image(raw)
    async with inference_lock:
        generated_caption, match = await asyncio.to_thread(analyse, image)
    return {"caption": generated_caption, "match": match}
