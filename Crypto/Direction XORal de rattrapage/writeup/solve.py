#!/usr/bin/env python3
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def decrypt(data, key):
    return bytes(byte ^ key[index % len(key)]
                 for index, byte in enumerate(data))


png_ciphertext = (DIST / "background.png.locked").read_bytes()
key = bytes(cipher ^ plain
            for cipher, plain in zip(png_ciphertext[:8], PNG_SIGNATURE))

background = decrypt(png_ciphertext, key)
music = decrypt((DIST / "music.mp3.locked").read_bytes(), key)
message = decrypt((DIST / "message_prof.txt.locked").read_bytes(), key)

assert background.startswith(PNG_SIGNATURE)
assert music[0] == 0xFF and music[1] & 0xE0 == 0xE0

flag = re.search(rb"CYBN\{[a-z0-9_]+\}", message)
if flag is None:
    raise ValueError("Flag not found")

print("Key  :", key.hex())
print("Flag :", flag.group().decode("ascii"))
