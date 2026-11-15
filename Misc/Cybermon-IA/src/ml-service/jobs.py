import asyncio
import secrets
import threading
import time
from pathlib import Path
from collections import deque
from contextlib import suppress
from storage import logger, save_metadata, utc_now


class JobQueue:
    """A bounded FIFO for one model worker; completed jobs expire from memory."""

    def __init__(self, analyse, max_pending=32, timeout=600, retention=600, archive_dir=None):
        self.analyse = analyse
        self.max_pending = max_pending
        self.timeout = timeout
        self.retention = retention
        self.jobs = {}
        self.pending = deque()
        self.ready = asyncio.Event()
        self.worker = None
        self.archive_dir = Path(archive_dir) if archive_dir else None

    def start(self):
        self.worker = asyncio.create_task(self.run())

    async def close(self):
        for job in self.jobs.values():
            job["cancel"].set()
            if job["status"] in ("queued", "processing"):
                self.finish(job, "cancelled", "Le scanner redémarre. Réessayez l'analyse.")
        if self.worker:
            self.worker.cancel()
            with suppress(asyncio.CancelledError):
                await self.worker

    def finish(self, job, status, error=None):
        ended = time.monotonic()
        job.update(
            status=status, error=error, raw=None, ended=ended, finishedAt=utc_now(),
            durationSeconds=round(ended - job["created"], 3),
            processingSeconds=round(ended - job["started"], 3) if "started" in job else 0,
        )
        self.save(job)
        logger.info(
            "event=finished session=%s job=%s status=%s bytes=%d wait_s=%.3f processing_s=%.3f total_s=%.3f error=%s",
            job["session"], job["id"], status, job["bytes"], job.get("waitSeconds", job["durationSeconds"]),
            job["processingSeconds"], job["durationSeconds"], repr(error),
        )
        job["done"].set()

    def save(self, job):
        try:
            save_metadata(job)
        except OSError:
            logger.exception("event=metadata_write_failed session=%s job=%s", job["session"], job["id"])

    def clean(self):
        now = time.monotonic()
        for key, job in list(self.jobs.items()):
            if job["status"] in ("queued", "processing") and now >= job["deadline"]:
                job["cancel"].set()
                self.finish(job, "failed", "Le délai maximal d'analyse est dépassé.")
            elif job.get("ended") is not None and now - job["ended"] >= self.retention:
                del self.jobs[key]
        self.pending = deque(key for key in self.pending if key in self.jobs and self.jobs[key]["status"] == "queued")

    def submit(self, raw, metadata=None):
        self.clean()
        if len(self.pending) >= self.max_pending:
            raise OverflowError("La file du scanner est pleine. Réessayez dans un instant.")
        key = secrets.token_hex(24)
        job = {
            "id": key, "raw": raw, "status": "queued", "stage": "queued",
            "progress": 0, "step": 0, "maxSteps": 24,
            "created": time.monotonic(), "deadline": time.monotonic() + self.timeout,
            "cancel": threading.Event(), "done": asyncio.Event(),
            "session": (metadata or {}).get("session", "direct"),
            "bytes": len(raw), "metadata": metadata or {}, "acceptedAt": utc_now(),
        }
        if self.archive_dir:
            directory = self.archive_dir / job["acceptedAt"][:10]
            directory.mkdir(parents=True, exist_ok=True)
            extension = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp"}.get(job["metadata"].get("mimeType"), ".bin")
            job["imagePath"] = directory / (key + extension)
            with job["imagePath"].open("xb") as image:
                image.write(raw)
            save_metadata(job)
        self.jobs[key] = job
        self.pending.append(key)
        logger.info(
            "event=accepted session=%s job=%s bytes=%d size=%sx%s position=%d image=%s",
            job["session"], key, len(raw), job["metadata"].get("width", "?"),
            job["metadata"].get("height", "?"), len(self.pending), job.get("imagePath", "not_archived"),
        )
        self.ready.set()
        return key

    def get(self, key):
        self.clean()
        job = self.jobs.get(key)
        if not job:
            return None
        result = {name: job[name] for name in ("id", "status", "stage", "progress", "step", "maxSteps")}
        result["position"] = list(self.pending).index(key) + 1 if job["status"] == "queued" else None
        result["elapsedSeconds"] = int(time.monotonic() - job["created"])
        if job["status"] == "done":
            result["result"] = job["result"]
        elif job["status"] in ("failed", "cancelled"):
            result["error"] = job["error"]
        return result

    def cancel(self, key):
        job = self.jobs.get(key)
        if job and job["status"] in ("queued", "processing"):
            job["cancel"].set()
            self.finish(job, "cancelled", "Analyse annulée.")
        self.clean()
        return self.get(key)

    def update(self, key, stage, progress, step):
        job = self.jobs.get(key)
        if job and job["status"] == "processing":
            changed_stage = job["stage"] != stage
            job.update(stage=stage, progress=max(job["progress"], progress), step=step)
            if changed_stage:
                self.save(job)
                logger.info("event=stage session=%s job=%s stage=%s progress=%.1f", job["session"], key, stage, job["progress"])

    async def run(self):
        loop = asyncio.get_running_loop()
        while True:
            await self.ready.wait()
            self.clean()
            if not self.pending:
                self.ready.clear()
                continue
            key = self.pending.popleft()
            job = self.jobs[key]
            job.update(status="processing", stage="encoding", progress=8, started=time.monotonic(), startedAt=utc_now())
            job["waitSeconds"] = round(job["started"] - job["created"], 3)
            self.save(job)
            logger.info("event=started session=%s job=%s bytes=%d wait_s=%.3f", job["session"], key, job["bytes"], job["waitSeconds"])

            def report(stage, progress, step=0):
                if job["cancel"].is_set() or time.monotonic() >= job["deadline"]:
                    raise TimeoutError()
                loop.call_soon_threadsafe(self.update, key, stage, progress, step)

            try:
                result = await asyncio.to_thread(self.analyse, job["raw"], report)
                if job["status"] == "processing":
                    if time.monotonic() >= job["deadline"]:
                        self.finish(job, "failed", "Le délai maximal d'analyse est dépassé.")
                    else:
                        job.update(result=result, stage="done", progress=100)
                        self.finish(job, "done")
            except TimeoutError:
                if job["status"] == "processing":
                    self.finish(job, "failed", "Le délai maximal d'analyse est dépassé.")
            except Exception:
                logger.exception("event=inference_failed session=%s job=%s", job["session"], key)
                if job["status"] == "processing":
                    self.finish(job, "failed", "Le scanner n'a pas pu analyser cette image.")
