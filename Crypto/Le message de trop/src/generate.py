import json
import math
import secrets
from pathlib import Path

from Crypto.Util.number import bytes_to_long, getPrime

FLAG = "CYBN{br04dc45t_1s_n0t_pr1v4t3}"
MESSAGE = (
    "ICI RADIO CYBERNIGHT. Colis au point Echo avant minuit. "
    f"Confirmez reception avec le code {FLAG}. Fin."
)
EXPONENTS = [7] * 7 + [5] * 4 + [3] * 2 + [11] * 2 + [13, 17, 19, 257, 65537]
OUTPUT = Path(__file__).resolve().parents[1] / "dist" / "messages.json"


message = MESSAGE.encode("ascii")
m = bytes_to_long(message)
assert 115 <= len(message) <= 125

exponents = EXPONENTS.copy()
secrets.SystemRandom().shuffle(exponents)
transmissions = []

for i, e in enumerate(exponents, 1):
    while True:
        p, q = getPrime(512), getPrime(512)
        n = p * q
        if (p != q
                and math.gcd(e, (p - 1) * (q - 1)) == 1
                and all(math.gcd(n, item["n"]) == 1 for item in transmissions)):
            break

    plaintext = m if e == 7 else bytes_to_long(secrets.token_bytes(119))

    transmissions.append({
        "id": f"RX-{i:03d}",
        "n": n,
        "e": e,
        "c": pow(plaintext, e, n),
    })

targets = [item for item in transmissions if item["e"] == 7]
product = math.prod(item["n"] for item in targets)
assert len(targets) == 7
assert all(m < item["n"] for item in targets)
assert product // min(item["n"] for item in targets) < m**7 < product

export = [{**item, "n": hex(item["n"]), "c": hex(item["c"])}
          for item in transmissions]
OUTPUT.parent.mkdir(exist_ok=True)
with OUTPUT.open("w", encoding="utf-8") as file:
    json.dump({"transmissions": export}, file, indent=2)

print(f"Generated {len(export)} transmissions in {OUTPUT}.")

