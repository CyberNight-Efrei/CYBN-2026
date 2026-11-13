#!/usr/bin/env python3
"""Supprime de CTFd les challenges qui n'ont plus de challenge*.yml dans le repo.

Usage : venv/bin/python PRUNE_CTFD.py [root] [--dry-run] [--max N]
À lancer depuis le dossier qui contient la config ctfcli (.ctf/).
"""

import argparse
import os
import sys
from pathlib import Path

import yaml
from ctfcli.core.api import API

EXCLUDED_DIRS = {"0-CHALL-TEMPLATE", "venv"}

# Même magasin de certificats que CLI_ALL.sh (CA interne de CTFd).
SYSTEM_CA = "/etc/ssl/certs/ca-certificates.crt"
if "REQUESTS_CA_BUNDLE" not in os.environ and os.access(SYSTEM_CA, os.R_OK):
    os.environ["REQUESTS_CA_BUNDLE"] = SYSTEM_CA


def find_challenge_files(root):
    for path in sorted(root.rglob("challenge*.yml")):
        parts = path.relative_to(root).parts[:-1]
        if any(p.startswith(".") or p in EXCLUDED_DIRS for p in parts):
            continue
        yield path


def local_names(root):
    names, errors = set(), []
    for path in find_challenge_files(root):
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            names.add(data["name"])
        except Exception as e:
            errors.append(f"{path}: {e}")
    return names, errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--max",
        type=int,
        default=5,
        help="Refuser de supprimer plus de N challenges d'un coup (défaut : 5)",
    )
    args = parser.parse_args()

    names, errors = local_names(Path(args.root).resolve())
    if errors:
        print("[ERREUR] challenge.yml illisibles, aucune suppression :", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1
    if not names:
        print("[ERREUR] Aucun challenge trouvé dans le repo, aucune suppression.", file=sys.stderr)
        return 1

    api = API()
    r = api.get("/api/v1/challenges?view=admin")
    r.raise_for_status()
    remote = r.json()["data"]

    stale = [c for c in remote if c["name"] not in names]
    print(f"[INFO] {len(names)} challenge(s) dans le repo, {len(remote)} sur CTFd.")

    if not stale:
        print("[OK] Aucun challenge à supprimer.")
        return 0

    for c in stale:
        print(f"[INFO] Absent du repo : #{c['id']} {c['name']} ({c.get('category')})")

    if len(stale) > args.max:
        print(
            f"[ERREUR] {len(stale)} suppressions > --max {args.max} : rien n'est supprimé.",
            file=sys.stderr,
        )
        return 1

    if args.dry_run:
        print("[OK] Simulation : rien n'est supprimé.")
        return 0

    failed = 0
    for c in stale:
        r = api.delete(f"/api/v1/challenges/{c['id']}")
        if r.ok:
            print(f"[OK] Supprimé : #{c['id']} {c['name']}")
        else:
            failed += 1
            print(f"[ERREUR] #{c['id']} {c['name']} : HTTP {r.status_code} {r.text[:200]}", file=sys.stderr)

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
