#!/usr/bin/env python3
"""Resolution automatique de Coeur de Fer (Web + Crypto).

Usage : python solve.py [http://localhost:8011]
"""
import sys

import requests

URL = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8011").rstrip("/")


def heart_sig(s):
    h = 0x1234
    for ch in s:
        h = ((h << 5) ^ (h >> 2) ^ ord(ch)) & 0xFFFF
    return h


def main():
    # 1) Signature cible de l'ame soeur (carte verrouillee).
    data = requests.get(URL + "/candidates").json()
    locked = next(p for p in data["profiles"] if p.get("locked"))
    target = int(locked["sig"], 16)

    # 2) Brute force d'un preimage (hash 16 bits -> trivial).
    i = 0
    while heart_sig("bot%d" % i) != target:
        i += 1
    forged = "bot%d" % i

    # 3) Declencher le match.
    r = requests.post(URL + "/match", data={"name": forged, "traits": ""}).json()
    assert r.get("matched"), r
    sm = r["soulmate"]
    enc = bytes.fromhex(sm["enc_numero"])
    key = sm["birthdate"].encode()

    # 4) Dechiffrer le numero : XOR repete avec la date de naissance.
    flag = bytes(enc[j] ^ key[j % len(key)] for j in range(len(enc))).decode()
    print("preimage :", forged, "(sig %04X)" % target)
    print("flag     :", flag)


if __name__ == "__main__":
    main()
