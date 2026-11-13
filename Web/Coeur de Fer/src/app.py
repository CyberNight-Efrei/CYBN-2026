import os
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 256 * 1024

FLAG = os.environ.get("FLAG", "CYBN{r0b0t_l0v3_x0r3d_h34rt}")

SOULMATE_NAME = "Vénus-9"
SOULMATE_BIRTH = "2041-07-14"
SOULMATE_SEED = "V3nus-9_my_0nly_l0ve"


def heart_sig(s):
    h = 0x1234
    for ch in s:
        h = ((h << 5) ^ (h >> 2) ^ ord(ch)) & 0xFFFF
    return h


def xor_hex(data_bytes, key_str):
    kb = key_str.encode()
    return bytes(b ^ kb[i % len(kb)] for i, b in enumerate(data_bytes)).hex()


SOULMATE_SIG = heart_sig(SOULMATE_SEED)
ENC_NUMERO = xor_hex(FLAG.encode(), SOULMATE_BIRTH)


CANDIDATES = [
    {"name": "Rouille-7", "model": "T-800 Romance Ed.", "age": 42, "city": "Secteur Fonderie", "online": True,
     "tagline": "Vieux modèle, cœur neuf.", "bio": "Aime les longues promenades près des hauts-fourneaux et les soirées huile de vidange.",
     "traits": ["humour", "chrome", "vintage"], "color": "#ff7a9c", "eyes": "round"},
    {"name": "Bolt-E", "model": "AutoCharme 3000", "age": 3, "city": "Station de Recharge 12", "online": True,
     "tagline": "Cherche quelqu'un pour partager sa batterie.", "bio": "Toujours à fond. Un peu trop parfois. Recharge-toi avec moi.",
     "traits": ["énergie", "optimiste", "rapide"], "color": "#7cf0d0", "eyes": "happy"},
    {"name": "Sprocket", "model": "MécaCœur v2", "age": 11, "city": "Atelier Sud", "online": False,
     "tagline": "Introverti mais bien huilé.", "bio": "Je préfère une bonne partie d'échecs à une rave de drones. Cherche quelqu'un de calme.",
     "traits": ["logique", "calme", "précis"], "color": "#ffd166", "eyes": "square"},
    {"name": "Nova-X", "model": "StellarBot L", "age": 7, "city": "Dôme Néon", "online": True,
     "tagline": "Danse le robot. Littéralement.", "bio": "La vie est une boîte de nuit. Rejoins-moi sur le dancefloor.",
     "traits": ["fun", "néon", "social"], "color": "#a98bff", "eyes": "star"},
    {"name": "Gearix", "model": "IndustriLove", "age": 19, "city": "Zone Portuaire", "online": False,
     "tagline": "Solide, fiable, un peu lourd en soirée.", "bio": "2 tonnes de tendresse. Je soulève des charges ET ton moral.",
     "traits": ["costaud", "loyal", "lent"], "color": "#8fd3ff", "eyes": "sleepy"},
]

TESTIMONIALS = [
    {"text": "Grâce à Cœur de Fer, j'ai trouvé l'amour de ma vie. On partage la même prise.", "by": "Bolt-E & une borne"},
    {"text": "3 semaines d'abonnement, 1 mariage. Et aucun court-circuit.", "by": "Rouille-7"},
    {"text": "Je cherchais une âme sœur compatible. L'algorithme a fait le reste.", "by": "Nova-X"},
]


def public_candidates():
    out = []
    for c in CANDIDATES:
        sig = heart_sig(c["name"] + "|" + ",".join(c["traits"]))
        out.append({**c, "sig": f"{sig:04X}", "locked": False})
    out.append({
        "name": "？？？",
        "model": "PROFIL PREMIUM VERROUILLÉ",
        "age": "??", "city": "Localisation masquée", "online": True,
        "tagline": "Votre âme sœur vous attend derrière ce profil.",
        "bio": "Ce membre premium n'est visible que par les robots dont le code d'affinité correspond exactement au sien.",
        "traits": ["？", "？", "？"],
        "color": "#ff4d94", "eyes": "mystery",
        "sig": f"{SOULMATE_SIG:04X}", "locked": True,
    })
    return out


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/candidates")
def candidates():
    return jsonify({"profiles": public_candidates(), "testimonials": TESTIMONIALS})


@app.route("/match", methods=["POST"])
def match():
    name = request.form.get("name", "")
    traits = request.form.get("traits", "")
    profile = name + "|" + traits if traits else name
    sig = heart_sig(profile)

    if sig == SOULMATE_SIG:
        return jsonify({
            "matched": True,
            "compatibility": 100,
            "your_sig": f"{sig:04X}",
            "reaction": "💘 MATCH PARFAIT ! Vénus-9 a accepté votre demande de connexion.",
            "soulmate": {
                "name": SOULMATE_NAME,
                "birthdate": SOULMATE_BIRTH,
                "enc_numero": ENC_NUMERO,
                "note": "Son numéro de série est chiffré (XOR) avec sa date de naissance.",
            },
        })

    diff = bin(sig ^ SOULMATE_SIG).count("1")
    compat = round(100 * (16 - diff) / 16)
    return jsonify({
        "matched": False,
        "compatibility": compat,
        "your_sig": f"{sig:04X}",
        "target_sig": f"{SOULMATE_SIG:04X}",
        "reaction": f"💔 Affinité {compat}%. Vénus-9 ne ressent pas d'étincelle...",
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
