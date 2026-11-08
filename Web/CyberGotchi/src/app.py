import os
import secrets
import sqlite3
import time
from pathlib import Path
from contextlib import contextmanager

from flask import Flask, jsonify, make_response, request, render_template
from models import COOLDOWN_SECONDS, MAX_LEVEL, Pet

app = Flask(__name__)
DB_PATH = os.environ.get("DATABASE_PATH", "/tmp/cybergotchi.db")
FLAG = os.environ.get("FLAG", "CYBN{BL00P_L3V3L_100_UNL0CK3D}")
COOKIE_NAME = "bloop_id"
ACTIONS = {"feed", "play", "train"}


@contextmanager
def db_connect():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10, isolation_level=None)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    with db_connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS pets (
                pet_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                xp INTEGER NOT NULL,
                level INTEGER NOT NULL,
                last_action REAL NOT NULL
            )
        """)


def read_pet(conn, pet_id):
    row = conn.execute("SELECT * FROM pets WHERE pet_id = ?", (pet_id,)).fetchone()
    return Pet(**dict(row)) if row else None


def write_pet(conn, pet):
    conn.execute(
        "UPDATE pets SET name = ?, xp = ?, level = ?, last_action = ? WHERE pet_id = ?",
        (pet.name, pet.xp, pet.level, pet.last_action, pet.pet_id),
    )


def current_pet(conn):
    pet_id = request.cookies.get(COOKIE_NAME, "")
    pet = read_pet(conn, pet_id) if len(pet_id) == 64 else None
    if pet:
        return pet, False
    pet = Pet(pet_id=secrets.token_hex(32))
    conn.execute(
        "INSERT INTO pets (pet_id, name, xp, level, last_action) VALUES (?, ?, ?, ?, ?)",
        (pet.pet_id, pet.name, pet.xp, pet.level, pet.last_action),
    )
    return pet, True


def response_with_cookie(data, status, pet, new_pet):
    response = make_response(jsonify(data), status)
    if new_pet:
        response.set_cookie(
            COOKIE_NAME, pet.pet_id, httponly=True, samesite="Lax", secure=request.is_secure
        )
    response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/health")
def health():
    return jsonify({"ok": True})


@app.get("/api/pet")
def get_pet():
    with db_connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        pet, new_pet = current_pet(conn)
        conn.commit()
    return response_with_cookie(pet.public_view(time.time()), 200, pet, new_pet)


@app.post("/api/action")
def do_action():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "JSON object required"}), 400
    action = payload.get("action")
    if action not in ACTIONS:
        return jsonify({"error": "Unknown action"}), 400

    with db_connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        pet, new_pet = current_pet(conn)
        now = time.time()
        remaining = max(0, int(pet.last_action + COOLDOWN_SECONDS - now + 0.999))
        if remaining:
            conn.commit()
            return response_with_cookie(
                {"error": "Cooldown active", "cooldown_remaining": remaining},
                429, pet, new_pet,
            )

        pet.gain_xp()
        pet.last_action = now

        # Vulnérabilité intentionnelle: mass assignment.
        # Le joueur doit découvrir la propriété 'level' dans les sources.
        # Les champs internes sont protégés, mais 'level' a été oublié.
        protected = {"pet_id", "xp", "last_action"}
        for field, value in payload.items():
            if field not in protected and hasattr(pet, field):
                setattr(pet, field, value)

        # On vérifie les types, sans éliminer le problème d'autorisation.
        if not isinstance(pet.level, int) or isinstance(pet.level, bool) or not 1 <= pet.level <= MAX_LEVEL:
            conn.rollback()
            return jsonify({"error": "Invalid pet state"}), 400
        if not isinstance(pet.name, str) or len(pet.name) > 24:
            conn.rollback()
            return jsonify({"error": "Invalid pet name"}), 400

        write_pet(conn, pet)
        conn.commit()

    return response_with_cookie(
        {"message": "Action completed", "pet": pet.public_view(time.time())},
        200, pet, new_pet,
    )


@app.get("/api/reward")
def reward():
    with db_connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        pet, new_pet = current_pet(conn)
        conn.commit()
    if pet.level < MAX_LEVEL:
        return response_with_cookie({"error": "BLOOP must reach level 100"}, 403, pet, new_pet)
    return response_with_cookie({"flag": FLAG}, 200, pet, new_pet)


init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
