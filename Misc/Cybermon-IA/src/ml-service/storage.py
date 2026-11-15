import json
import logging
import sys
import time
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path

logger = logging.getLogger("cybermon.ml")


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def configure_logging(directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    formatter = logging.Formatter("%(asctime)sZ %(levelname)s %(message)s", "%Y-%m-%dT%H:%M:%S")
    formatter.converter = time.gmtime
    if not logger.handlers:
        file_handler = RotatingFileHandler(directory / "scanner.log", maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8")
        for handler in (logging.StreamHandler(sys.stdout), file_handler):
            handler.setFormatter(formatter)
            logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False


def save_metadata(job):
    if not job.get("imagePath"):
        return
    data = {key: job[key] for key in (
        "id", "session", "bytes", "metadata", "status", "stage", "progress", "step",
        "acceptedAt", "startedAt", "finishedAt", "waitSeconds", "processingSeconds",
        "durationSeconds", "result", "error",
    ) if key in job}
    data["image"] = job["imagePath"].name
    path = job["imagePath"].with_suffix(".json")
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)
