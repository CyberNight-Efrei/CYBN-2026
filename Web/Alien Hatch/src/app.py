import os
import re
import sqlite3
import time
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 256 * 1024

DB1 = "/tmp/alien1.db"
DB2 = "/tmp/alien2.db"
DB3 = "/tmp/alien3.db"

FLAG1 = os.environ["FLAG1"]
FLAG2 = os.environ["FLAG2"]
FLAG3 = os.environ["FLAG3"]

FOODS = [
    ("Nebulonite", 12, 6),
    ("Cristaux", 16, 7),
    ("Plasma", 26, 8),
    ("Algues de Mars", 5, 2),
    ("Meteorite", 30, 5),
    ("Chaussette spatiale", 0, -5),
]


def build_db(path, flag, noise_label, noise_value):
    if os.path.exists(path):
        os.remove(path)
    conn = sqlite3.connect(path)
    c = conn.cursor()
    c.execute("CREATE TABLE foods (id INTEGER PRIMARY KEY, name TEXT, calories INTEGER, yumminess INTEGER)")
    c.executemany("INSERT INTO foods (name, calories, yumminess) VALUES (?, ?, ?)", FOODS)
    c.execute("CREATE TABLE secrets (id INTEGER PRIMARY KEY, label TEXT, value TEXT)")
    c.execute("INSERT INTO secrets (label, value) VALUES (?, ?)", (noise_label, noise_value))
    c.execute("INSERT INTO secrets (label, value) VALUES (?, ?)", ("drapeau", flag))
    conn.commit()
    conn.close()


def init_db():
    build_db(DB1, FLAG1, "rapport_xenobiologie", "Ce specimen ingere absolument n'importe quoi.")
    build_db(DB2, FLAG2, "note_securite", "Le sas digestif filtre certaines substances.")
    build_db(DB3, FLAG3, "observation", "Zorglub ne montre plus aucune reaction visible.")


def get_db(path):
    conn = sqlite3.connect(path, timeout=1.0)
    conn.row_factory = sqlite3.Row

    # Limites anti-abus : les 3 SQLi volontaires restent exploitables.
    conn.setlimit(sqlite3.SQLITE_LIMIT_SQL_LENGTH, 4096)
    conn.setlimit(sqlite3.SQLITE_LIMIT_LENGTH, 64 * 1024)
    deadline = time.monotonic() + 3  # secondes par requête SQL
    conn.set_progress_handler(lambda: int(time.monotonic() > deadline), 1000)
    return conn


def digest_rows(rows):
    total_cal = 0
    digested = []
    for r in rows:
        try:
            total_cal += int(r["calories"]) if r["calories"] is not None else 0
        except (ValueError, TypeError):
            pass
        digested.append({"name": r["name"], "calories": r["calories"], "yumminess": r["yumminess"]})
    return total_cal, digested


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/menu")
def menu():
    conn = get_db(DB1)
    rows = conn.execute("SELECT name FROM foods").fetchall()
    conn.close()
    return jsonify([r["name"] for r in rows])


@app.route("/feed", methods=["POST"])
def feed():
    food_name = request.form.get("food", "")
    query = f"SELECT name, calories, yumminess FROM foods WHERE name = '{food_name}'"

    conn = get_db(DB1)
    rows, sql_error = [], None
    try:
        rows = conn.execute(query).fetchmany(32)
    except Exception as e:
        sql_error = str(e)
    conn.close()

    if sql_error:
        return jsonify({
            "status": "error",
            "reaction": "🤮 KRRRZZT ! Zorglub régurgite une anomalie cosmique...",
            "calories": 0, "digested": [], "vomit": sql_error,
        })
    if rows:
        total_cal, digested = digest_rows(rows)
        return jsonify({
            "status": "ok",
            "reaction": f"😋 Zorglub a absorbé : {digested[0]['name']}",
            "calories": total_cal, "digested": digested, "vomit": None,
        })
    return jsonify({
        "status": "unknown",
        "reaction": f"🛸 Zorglub renifle « {food_name} »... et refuse d'y toucher.",
        "calories": 0, "digested": [], "vomit": None,
    })


def sas_filter(s):
    s = re.sub(r"union", "", s, flags=re.I)
    s = re.sub(r"select", "", s, flags=re.I)
    return s


@app.route("/feed2", methods=["POST"])
def feed2():
    food_name = sas_filter(request.form.get("food", ""))
    query = f"SELECT name, calories, yumminess FROM foods WHERE name = '{food_name}'"

    conn = get_db(DB2)
    rows, sql_error = [], None
    try:
        rows = conn.execute(query).fetchmany(32)
    except Exception as e:
        sql_error = str(e)
    conn.close()

    if sql_error:
        return jsonify({
            "status": "error",
            "reaction": "🤮 BLAARG ! Le sas digestif de Zorglub a un raté...",
            "calories": 0, "digested": [], "vomit": sql_error,
        })
    if rows:
        total_cal, digested = digest_rows(rows)
        return jsonify({
            "status": "ok",
            "reaction": f"😋 Zorglub a filtré puis absorbé : {digested[0]['name']}",
            "calories": total_cal, "digested": digested, "vomit": None,
        })
    return jsonify({
        "status": "unknown",
        "reaction": "🛸 Le sas digestif rejette cette substance.",
        "calories": 0, "digested": [], "vomit": None,
    })


@app.route("/feed3", methods=["POST"])
def feed3():
    food_name = request.form.get("food", "")
    query = f"SELECT name FROM foods WHERE name = '{food_name}'"

    conn = get_db(DB3)
    try:
        rows = conn.execute(query).fetchmany(32)
        conn.close()
    except Exception:
        conn.close()
        return jsonify({"status": "sick", "reaction": "🤢 Zorglub a un haut-le-cœur silencieux..."})

    if rows:
        return jsonify({"status": "ok", "reaction": "😋 Zorglub mange avec appétit."})
    return jsonify({"status": "nope", "reaction": "🛸 Zorglub recrache et refuse."})


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=False)
