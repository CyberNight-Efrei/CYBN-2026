#!/usr/bin/env python3
import hashlib
import sys

def keystream(password: bytes, length: int) -> bytes:
    out = b""
    counter = 0
    while len(out) < length:
        out += hashlib.sha256(b"key:" + password + counter.to_bytes(4, "big")).digest()
        counter += 1
    return out[:length]

def c_array(data: bytes) -> str:
    return ", ".join(f"0x{b:02x}" for b in data)


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit("usage: gen_secret.py PASSWORD FLAG")
    password = sys.argv[1].encode()
    flag = sys.argv[2].encode()

    check = hashlib.sha256(b"check:" + password).digest()
    enc = bytes(a ^ b for a, b in zip(flag, keystream(password, len(flag))))

    print("/* Fichier généré par gen_secret.py, ne pas éditer. */")
    print(f"static const unsigned char CHECK_HASH[32] = {{ {c_array(check)} }};")
    print(f"static const unsigned char ENC_FLAG[{len(enc)}] = {{ {c_array(enc)} }};")
    print(f"#define ENC_FLAG_LEN {len(enc)}")


if __name__ == "__main__":
    main()
