import json
import os
import secrets
import time
import warnings
from math import isqrt

import jwt
import requests
from flask import Flask, Response, abort, jsonify, request, send_from_directory
from Crypto.PublicKey import RSA
from Crypto.Util.number import isPrime
from cryptography.hazmat.primitives.serialization import load_pem_public_key

warnings.filterwarnings("ignore", message=r".*RSA key is .* bits long.*")

FLAG = "CYBN{PouRtAnt_Je_lai_b1en_sEcurisE_aVEc_le_cadeNAS}"
HOST = "0.0.0.0"
PORT = 8080
INTERNAL_BASE = f"http://127.0.0.1:{PORT}"
TONDEUSES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tondeuses")
BANNER = "banner.jpg"
LA_VEGAN = "la_vegan.jpg"
LA_CLASSIQUE = "la_classique.jpg"
LA_GROSSE_BERTHA = "la_grosse_bertha.jpg"
TONDEUSES = [LA_VEGAN, LA_CLASSIQUE, LA_GROSSE_BERTHA]
KID = "tondeuse-rsa-1"
PRIME_BITS = 256

FERMAT_ITERATIONS = 4  # O_o

def fermat_iterations(n: int) -> int:
    a = isqrt(n)
    if a * a < n:
        a += 1
    count = 0
    while True:
        count += 1
        b2 = a * a - n
        r = isqrt(b2)
        if r * r == b2:
            return count
        a += 1


def generate_weak_key() -> RSA.RsaKey:
    k = FERMAT_ITERATIONS
    e = 65537
    while True:
        a_mid = secrets.randbits(PRIME_BITS) | (1 << (PRIME_BITS - 1))
        b_lo = isqrt(2 * (k - 1) * a_mid - (k - 1) ** 2) + 1
        b_hi = isqrt(2 * k * a_mid - k ** 2)
        if b_lo > b_hi:
            continue
        b = b_lo + secrets.randbelow(b_hi - b_lo + 1)
        while b <= b_hi:
            p, q = a_mid - b, a_mid + b
            if p > 2 and isPrime(p) and isPrime(q):
                phi = (p - 1) * (q - 1)
                try:
                    d = pow(e, -1, phi)
                except ValueError:
                    b += 1
                    continue
                n = p * q
                if fermat_iterations(n) != k:
                    b += 1
                    continue
                if p < q:
                    p, q = q, p
                return RSA.construct((n, e, d, p, q))
            b += 1


PRIVATE_KEY = generate_weak_key()
PRIVATE_PEM = PRIVATE_KEY.export_key("PEM")

_pub = load_pem_public_key(PRIVATE_KEY.publickey().export_key("PEM"))
_jwk = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(_pub))
_jwk.update({"use": "sig", "alg": "RS256", "kid": KID})
JWKS = {"keys": [_jwk]}

_jwks_cache = None


def get_jwks() -> dict:
    global _jwks_cache
    if _jwks_cache is None:
        try:
            _jwks_cache = requests.get(f"{INTERNAL_BASE}/jwk", timeout=3).json()
        except Exception:
            _jwks_cache = JWKS
    return _jwks_cache


def make_guest_token() -> str:
    now = int(time.time())
    payload = {"user": "guest", "role": "guest", "iat": now, "exp": now + 3600}
    return jwt.encode(payload, PRIVATE_PEM, algorithm="RS256", headers={"kid": KID})


def verify_token(token: str):
    try:
        kid = jwt.get_unverified_header(token).get("kid")
        jwk = next((k for k in get_jwks()["keys"] if k.get("kid") == kid), None)
        if jwk is None:
            return None
        public_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(jwk))
        return jwt.decode(token, public_key, algorithms=["RS256"])
    except Exception:
        return None


def current_identity():
    token = request.cookies.get("token")
    return verify_token(token) if token else None

app = Flask(__name__)


@app.route("/")
def index():
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "index.html"), "r", encoding="utf-8") as f:
        html = f.read()

    resp = Response(html, content_type="text/html; charset=utf-8")
    if current_identity() is None:
        resp.set_cookie("token", make_guest_token(), httponly=False, samesite="Lax")
    return resp


@app.route("/me")
def me():
    identity = current_identity()
    if identity is None:
        return jsonify({"user": None, "role": "anonymous"})
    return jsonify({"user": identity.get("user"), "role": identity.get("role")})

@app.route("/catalogue")
def catalogue():
    items = []
    for name in TONDEUSES:
        internal = f"{INTERNAL_BASE}/tondeuses_granting_service/{name}"
        items.append(
            {
                "name": name.rsplit(".", 1)[0].replace("_", " ").title(),
                "file": name,
                "img": "/get_tondeuse?url=" + requests.utils.quote(internal, safe=""),
            }
        )
    return jsonify(items)

@app.route("/get_tondeuse")
def get_tondeuse():
    url = request.args.get("url", "")
    if not url:
        abort(400, "paramètre 'url' manquant")
    try:
        upstream = requests.get(url, timeout=4)
    except requests.RequestException as exc:
        return Response(f"fetch error: {exc}", status=502)
    content_type = upstream.headers.get("Content-Type", "application/octet-stream")
    return Response(upstream.content, status=upstream.status_code, content_type=content_type)


@app.route("/tondeuses_granting_service/<path:name>")
def tondeuses_granting_service(name):
    if name not in TONDEUSES + [BANNER]:
        abort(404)
    return send_from_directory(TONDEUSES_DIR, name)


@app.route("/jwk")
def jwk():
    if request.remote_addr not in ("127.0.0.1", "::1"):
        abort(403, "forbidden: localhost only")
    return jsonify(JWKS)

@app.route("/admin")
def admin():
    identity = current_identity()
    if identity is None:
        return jsonify({"error": "no valid session"}), 401
    if identity.get("role") != "admin":
        return jsonify({"error": "forbidden", "role": identity.get("role")}), 403
    return jsonify({"message": "Bienvenue admin.", "flag": FLAG})


if __name__ == "__main__":
    app.run(host=HOST, port=PORT, threaded=True)
