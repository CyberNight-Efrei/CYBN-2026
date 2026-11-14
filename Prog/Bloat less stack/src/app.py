import json
import os
import re
import resource
import shutil
import subprocess
import tempfile

from fastapi import FastAPI, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse


JAIL = os.environ.get("JAIL_DIR", "/srv/jail")
WORKBASE = "/sandbox" if os.path.isdir("/sandbox") else tempfile.gettempdir()

RUN_TIMEOUT = 5
BUILD_TIMEOUT = 10
MAX_SRC = 64 * 1024
MAX_OUT = 32 * 1024
FORBIDDEN = ("%include", "incbin", "%pathsearch", "%depend")
ALLOWED_SYSCALLS = {0, 1, 2, 3, 4, 5, 6, 8, 9, 12, 17, 19, 20, 40, 60,
                    78, 79, 80, 81, 217, 231, 257, 262}
MOV_RAX = re.compile(r"\tmov(?:abs)?\s+(?:rax|eax|ax|al),(0x[0-9a-f]+)$", re.M)
BACKGROUND = os.path.join(os.path.dirname(os.path.abspath(__file__)), "background.jpg")
TOTORO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "totoro.gif")
INDEX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")


def _limits() -> None:
    resource.setrlimit(resource.RLIMIT_CPU, (2, 2))
    resource.setrlimit(resource.RLIMIT_AS, (256 * 1024 * 1024,) * 2)
    resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))


def run_asm(code: str) -> dict:
    if not code.strip():
        return {"ok": False, "stage": "source", "output": "Source vide."}
    if len(code) > MAX_SRC:
        return {"ok": False, "stage": "source", "output": "Source trop longue."}
    low = code.lower()
    for bad in FORBIDDEN:
        if bad in low:
            return {"ok": False, "stage": "source",
                    "output": f"Directive interdite dans ce bac à sable : {bad}\n"
                              "Lis le fichier à l'exécution (syscalls), pas à l'assemblage."}

    for tool in ("nasm", "ld", "objdump"):
        if shutil.which(tool) is None:
            return {"ok": False, "stage": "env",
                    "output": f"Outil manquant côté serveur : {tool}."}
    if not os.path.isdir(JAIL):
        return {"ok": False, "stage": "env",
                "output": f"Répertoire de travail introuvable : {JAIL}.\n"
                          "En local (hors Docker), crée-le et pointe JAIL_DIR dessus."}

    work = tempfile.mkdtemp(dir=WORKBASE)
    try:
        asm = os.path.join(work, "p.asm")
        obj = os.path.join(work, "p.o")
        binp = os.path.join(work, "p")
        with open(asm, "w") as f:
            f.write(code)

        def clean(msg: str) -> str:
            return msg.replace(work + "/", "").replace(work, "").strip()

        r = subprocess.run(["nasm", "-f", "elf64", asm, "-o", obj],
                           cwd=work, capture_output=True, text=True, timeout=BUILD_TIMEOUT)
        if r.returncode != 0:
            return {"ok": False, "stage": "nasm", "output": clean(r.stderr or r.stdout)}

        r = subprocess.run(["objdump", "-d", "-M", "intel", "--no-show-raw-insn", obj],
                           cwd=work, capture_output=True, text=True, timeout=BUILD_TIMEOUT)
        if r.returncode != 0:
            return {"ok": False, "stage": "env", "output": "Désassemblage impossible côté serveur."}
        bad = sorted({int(n, 16) for n in MOV_RAX.findall(r.stdout)} - ALLOWED_SYSCALLS)
        if bad:
            return {"ok": False, "stage": "syscall",
                    "output": f"Syscall interdit ! : {', '.join(map(str, bad))}\n"
                              f"Autorisés : {', '.join(map(str, sorted(ALLOWED_SYSCALLS)))}"}

        r = subprocess.run(["ld", obj, "-o", binp],
                           cwd=work, capture_output=True, text=True, timeout=BUILD_TIMEOUT)
        if r.returncode != 0:
            return {"ok": False, "stage": "ld", "output": clean(r.stderr or r.stdout)}
        os.chmod(binp, 0o700)

        try:
            r = subprocess.run([binp], cwd=JAIL, stdin=subprocess.DEVNULL,
                               capture_output=True, timeout=RUN_TIMEOUT, preexec_fn=_limits)
        except subprocess.TimeoutExpired:
            return {"ok": False, "stage": "run",
                    "output": f"Temps dépassé (> {RUN_TIMEOUT}s). Boucle infinie ?"}

        out = r.stdout.decode("utf-8", "replace")
        err = r.stderr.decode("utf-8", "replace")
        text = out
        if err:
            text += "\n--- stderr ---\n" + err
        if r.returncode:
            if r.returncode < 0:
                text += f"\n[tué par le signal {-r.returncode}]"
            else:
                text += f"\n[code de sortie : {r.returncode}]"
        if len(text) > MAX_OUT:
            text = text[:MAX_OUT] + "\n...[sortie tronquée]"
        return {"ok": True, "stage": "run", "output": text.strip() or "(aucune sortie)"}
    finally:
        shutil.rmtree(work, ignore_errors=True)


app = FastAPI(title="Bloat less stack", docs_url=None, redoc_url=None, openapi_url=None)


@app.get("/", response_class=HTMLResponse)
async def index() -> HTMLResponse:
    return HTMLResponse(PAGE)


@app.get("/background.jpg")
async def background() -> FileResponse:
    return FileResponse(BACKGROUND, media_type="image/jpeg",
                        headers={"Cache-Control": "public, max-age=86400"})


@app.get("/totoro.gif")
async def totoro() -> FileResponse:
    return FileResponse(TOTORO, media_type="image/gif",
                        headers={"Cache-Control": "public, max-age=86400"})


@app.post("/run")
async def run(request: Request) -> JSONResponse:
    try:
        data = await request.json()
        code = str(data.get("code", ""))
    except Exception:
        return JSONResponse({"ok": False, "stage": "source", "output": "Requête invalide."})
    try:
        result = await run_in_threadpool(run_asm, code)
    except Exception as e:
        result = {"ok": False, "stage": "server", "output": f"Erreur serveur : {e}"}
    return JSONResponse(result)


STARTER = """I hired :
to stare at you.
"""

with open(INDEX, encoding="utf-8") as f:
    PAGE = f.read().replace("%STARTER%", json.dumps(STARTER))
