
import os
import sqlite3
import secrets
import hashlib

from uuid import uuid4
from contextlib import closing

from flask import (
    Flask,
    render_template,
    jsonify,
    request,
    session
)

app = Flask(__name__)


# ==========================================
# CONFIGURATION
# ==========================================

app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY",
    secrets.token_hex(32)
)

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax"
)

# Base SQLite temporaire dans Docker
DB_PATH = "/tmp/cybernight.db"

# Solde initial
INITIAL_BALANCE = 100

# Prix des billets
PRICES = {
    "standard": 50,
    "vip": 150
}

# Récompense du challenge
FLAG = os.environ.get("CHALLENGE_FLAG")

if not FLAG or not FLAG.startswith("CYBN{") or not FLAG.endswith("}"):
    raise RuntimeError(
        "CHALLENGE_FLAG doit être défini au format CYBN{...}"
    )


# ==========================================
# CONNEXION SQLITE
# ==========================================

def get_db():

    conn = sqlite3.connect(
        DB_PATH,
        timeout=10
    )

    conn.row_factory = sqlite3.Row

    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 10000")

    return conn


# ==========================================
# INITIALISATION DE LA BASE
# ==========================================

def init_db():

    with closing(get_db()) as conn:

        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                balance INTEGER NOT NULL
                    CHECK (balance >= 0)
            );

            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                type TEXT NOT NULL,
                price INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',

                FOREIGN KEY (user_id)
                    REFERENCES users(id),

                CHECK (type IN ('standard', 'vip')),
                CHECK (status IN ('active', 'refunded'))
            );

            CREATE INDEX IF NOT EXISTS idx_tickets_user
            ON tickets(user_id);

            CREATE TABLE IF NOT EXISTS minigame (
                user_id TEXT PRIMARY KEY,
                claimed INTEGER NOT NULL DEFAULT 0,

                FOREIGN KEY (user_id)
                    REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS promo_codes (
                user_id TEXT PRIMARY KEY,
                code TEXT NOT NULL,
                redeemed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (user_id)
                    REFERENCES users(id)
            );
        """)

        conn.commit()


# ==========================================
# IDENTIFICATION DU JOUEUR
# ==========================================

def get_user_id():

    user_id = session.get("user_id")

    if user_id is None:
        user_id = str(uuid4())
        session["user_id"] = user_id

    # Créer un portefeuille pour chaque joueur
    with closing(get_db()) as conn:

        conn.execute("""
            INSERT OR IGNORE INTO users (id, balance)
            VALUES (?, ?)
        """, (user_id, INITIAL_BALANCE))

        conn.commit()

    return user_id


# ==========================================
# ROUTES PRINCIPALES
# ==========================================

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/health")
def health():

    return jsonify({
        "status": "ok",
        "challenge": "Race Condition"
    })


# ==========================================
# CONSULTATION DU PORTEFEUILLE
# ==========================================

@app.route("/api/wallet", methods=["GET"])
def get_wallet():

    user_id = get_user_id()

    with closing(get_db()) as conn:

        user = conn.execute("""
            SELECT balance
            FROM users
            WHERE id = ?
        """, (user_id,)).fetchone()

        tickets = conn.execute("""
            SELECT id, type, price, status
            FROM tickets
            WHERE user_id = ?
            ORDER BY id
        """, (user_id,)).fetchall()

        return jsonify({
            "balance": user["balance"],
            "tickets": [
                dict(ticket)
                for ticket in tickets
            ]
        })


# ==========================================
# ACHAT DE BILLETS
# ==========================================

@app.route("/api/buy", methods=["POST"])
def buy_ticket():

    user_id = get_user_id()

    data = request.get_json(silent=True) or {}
    ticket_type = data.get("ticket_type")

    if ticket_type not in PRICES:
        return jsonify({
            "success": False,
            "message": "Type de billet invalide."
        }), 400

    price = PRICES[ticket_type]

    with closing(get_db()) as conn:

        try:
            # Transaction sécurisée pour les achats
            conn.execute("BEGIN IMMEDIATE")

            user = conn.execute("""
                SELECT balance
                FROM users
                WHERE id = ?
            """, (user_id,)).fetchone()

            balance = user["balance"]

            if balance < price:

                conn.rollback()

                missing = price - balance

                return jsonify({
                    "success": False,
                    "message": (
                        f"Solde insuffisant. Il te manque "
                        f"{missing} crédits pour obtenir ce billet."
                    ),
                    "balance": balance,
                    "missing": missing
                }), 400

            # Débiter le portefeuille
            new_balance = balance - price

            conn.execute("""
                UPDATE users
                SET balance = ?
                WHERE id = ?
            """, (new_balance, user_id))

            # Créer le billet
            cursor = conn.execute("""
                INSERT INTO tickets (
                    user_id,
                    type,
                    price,
                    status
                )
                VALUES (?, ?, ?, 'active')
            """, (user_id, ticket_type, price))

            ticket_id = cursor.lastrowid

            conn.commit()

            return jsonify({
                "success": True,
                "message": "Billet acheté avec succès !",
                "balance": new_balance,
                "ticket": {
                    "id": ticket_id,
                    "type": ticket_type,
                    "price": price,
                    "status": "active"
                }
            }), 200

        except sqlite3.Error:

            conn.rollback()
            app.logger.exception("Erreur SQL pendant l'achat")

            return jsonify({
                "success": False,
                "message": "Erreur lors de l'achat."
            }), 500


# ==========================================
# REMBOURSEMENT DES BILLETS
# VULNÉRABILITÉ VOLONTAIRE : TOCTOU
# ==========================================

@app.route("/api/refund", methods=["POST"])
def refund_ticket():

    user_id = get_user_id()

    data = request.get_json(silent=True) or {}
    ticket_id = data.get("ticket_id")

    if type(ticket_id) is not int or ticket_id <= 0:
        return jsonify({
            "success": False,
            "message": "Identifiant de billet invalide."
        }), 400

    with closing(get_db()) as conn:

        # ==================================
        # TIME OF CHECK
        # ==================================
        # Vérification du statut du billet
        # AVANT le début de la transaction.

        ticket = conn.execute("""
            SELECT id, type, price, status
            FROM tickets
            WHERE id = ?
            AND user_id = ?
        """, (ticket_id, user_id)).fetchone()

        if ticket is None:
            return jsonify({
                "success": False,
                "message": "Billet introuvable."
            }), 404

        if ticket["type"] != "standard":
            return jsonify({
                "success": False,
                "message": "Ce billet n'est pas remboursable."
            }), 400

        if ticket["status"] == "refunded":
            return jsonify({
                "success": False,
                "message": "Ce billet a déjà été remboursé."
            }), 409

        # ==================================
        # TIME OF USE
        # ==================================
        # VULNÉRABILITÉ VOLONTAIRE :
        # Le statut n'est pas revérifié
        # dans la transaction d'écriture.
        #
        # Deux requêtes concurrentes peuvent
        # avoir lu le même statut "active".

        try:
            conn.execute("BEGIN IMMEDIATE")

            # Créditer le portefeuille
            conn.execute("""
                UPDATE users
                SET balance = balance + ?
                WHERE id = ?
            """, (ticket["price"], user_id))

            # Marquer le billet comme remboursé
            conn.execute("""
                UPDATE tickets
                SET status = 'refunded'
                WHERE id = ?
                AND user_id = ?
            """, (ticket_id, user_id))

            conn.commit()

            balance = conn.execute("""
                SELECT balance
                FROM users
                WHERE id = ?
            """, (user_id,)).fetchone()["balance"]

            return jsonify({
                "success": True,
                "message": (
                    f"Remboursement effectué ! "
                    f"+{ticket['price']} crédits."
                ),
                "balance": balance,
                "ticket": {
                    "id": ticket["id"],
                    "type": ticket["type"],
                    "price": ticket["price"],
                    "status": "refunded"
                }
            }), 200

        except sqlite3.Error:

            conn.rollback()
            app.logger.exception(
                "Erreur SQL pendant le remboursement"
            )

            return jsonify({
                "success": False,
                "message": "Erreur lors du remboursement."
            }), 500


# ==========================================
# MINI-JEU : TROUVER LE TICKET GAGNANT
# ==========================================

@app.route("/api/minigame", methods=["POST"])
def minigame():

    user_id = get_user_id()

    data = request.get_json(silent=True) or {}
    choice = data.get("choice")

    if type(choice) is not int or choice not in (0, 1, 2):
        return jsonify({
            "success": False,
            "message": "Choix invalide."
        }), 400

    with closing(get_db()) as conn:

        try:
            conn.execute("BEGIN IMMEDIATE")

            # Vérifier si le bonus a déjà été obtenu
            claimed = conn.execute("""
                SELECT claimed
                FROM minigame
                WHERE user_id = ?
            """, (user_id,)).fetchone()

            if claimed and claimed["claimed"]:

                conn.rollback()

                return jsonify({
                    "success": False,
                    "message": (
                        "Tu as déjà obtenu ton bonus de 10 crédits."
                    )
                }), 409

            # Déterminer le gobelet gagnant
            # Le résultat reste identique pour ce joueur
            winning = int.from_bytes(
                hashlib.sha256(
                    user_id.encode()
                ).digest()[:4],
                "big"
            ) % 3

            if choice != winning:

                conn.rollback()

                return jsonify({
                    "success": False,
                    "message": (
                        "Raté ! Le ticket n'était pas "
                        "sous ce gobelet."
                    )
                }), 200

            # Enregistrer le gain unique
            conn.execute("""
                INSERT INTO minigame (user_id, claimed)
                VALUES (?, 1)
                ON CONFLICT(user_id)
                DO UPDATE SET claimed = 1
            """, (user_id,))

            # Ajouter les 10 crédits
            conn.execute("""
                UPDATE users
                SET balance = balance + 10
                WHERE id = ?
            """, (user_id,))

            conn.commit()

            return jsonify({
                "success": True,
                "message": (
                    "Bravo ! Tu as gagné 10 crédits !"
                )
            }), 200

        except sqlite3.Error:

            conn.rollback()
            app.logger.exception("Erreur mini-jeu")

            return jsonify({
                "success": False,
                "message": "Erreur lors du mini-jeu."
            }), 500


# ==========================================
# CODE PROMOTIONNEL : CYBN2026
# ==========================================

@app.route("/api/promo", methods=["POST"])
def apply_promo():
    user_id = get_user_id()
    data = request.get_json(silent=True) or {}
    code = data.get("code")

    if not isinstance(code, str):
        return jsonify({
            "success": False,
            "message": "Code promotionnel invalide."
        }), 400

    code = code.strip().upper()
    if code != "CYBN2026":
        return jsonify({
            "success": False,
            "message": "Ce code promotionnel est invalide."
        }), 400

    with closing(get_db()) as conn:
        try:
            # Validation et crédit atomiques : usage unique même en concurrence.
            conn.execute("BEGIN IMMEDIATE")

            existing = conn.execute("""
                SELECT user_id FROM promo_codes WHERE user_id = ?
            """, (user_id,)).fetchone()

            if existing is not None:
                conn.rollback()
                return jsonify({
                    "success": False,
                    "message": "Tu as déjà utilisé ce code promo."
                }), 409

            conn.execute("""
                INSERT INTO promo_codes (user_id, code)
                VALUES (?, ?)
            """, (user_id, code))

            conn.execute("""
                UPDATE users
                SET balance = balance + 10
                WHERE id = ?
            """, (user_id,))

            balance = conn.execute("""
                SELECT balance FROM users WHERE id = ?
            """, (user_id,)).fetchone()["balance"]

            conn.commit()
            return jsonify({
                "success": True,
                "message": "Code CYBN2026 appliqué ! +10 crédits.",
                "balance": balance
            }), 200

        except sqlite3.Error:
            conn.rollback()
            app.logger.exception("Erreur code promo")
            return jsonify({
                "success": False,
                "message": "Erreur lors de l'application du code."
            }), 500


# ==========================================
# RÉCOMPENSE VIP
# ==========================================

@app.route("/api/reward", methods=["GET"])
def get_reward():

    user_id = get_user_id()

    with closing(get_db()) as conn:

        # Rechercher un billet VIP appartenant
        # au joueur connecté
        vip_ticket = conn.execute("""
            SELECT id
            FROM tickets
            WHERE user_id = ?
              AND type = 'vip'
              AND status = 'active'
            LIMIT 1
        """, (user_id,)).fetchone()

        if vip_ticket is None:
            return jsonify({
                "success": False,
                "message": (
                    "Accès réservé aux détenteurs "
                    "d'un billet VIP."
                )
            }), 403

        return jsonify({
            "success": True,
            "message": "Bienvenue dans l'espace VIP !",
            "flag": FLAG,
            "ticket_id": vip_ticket["id"]
        }), 200


# ==========================================
# DÉMARRAGE DU SERVEUR
# ==========================================

init_db()

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=8080,
        threaded=True
    )
