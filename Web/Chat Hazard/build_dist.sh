#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

NAME="chat-hazard"
ZIP="dist/${NAME}-src.zip"
FAKE_FLAG='CYBN{fake_flag}'
REAL_FLAG=$(sed -n 's/.*FLAG[:=] *"\(CYBN{[^"}]*}\)".*/\1/p' docker-compose.yml | head -n1)

mkdir -p dist
rm -f "$ZIP"

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

mkdir -p "$tmp/$NAME"
cp -r src "$tmp/$NAME/"

# Les joueurs reçoivent de quoi lancer le chall, mais jamais le vrai flag.
for file in Dockerfile docker-compose.yml; do
    sed "s|CYBN{[^\"}]*}|$FAKE_FLAG|g" "$file" > "$tmp/$NAME/$file"
done

# Garde-fou : on refuse de livrer une archive qui contient le flag.
if [ -n "$REAL_FLAG" ] && grep -rqF "$REAL_FLAG" "$tmp/$NAME"; then
    echo "Erreur : le flag se trouve dans l'archive, abandon." >&2
    exit 1
fi

(cd "$tmp" && zip -qr "${NAME}-src.zip" "$NAME")
mv "$tmp/${NAME}-src.zip" dist/

echo "$ZIP"
unzip -l "$ZIP" | tail -n +2
