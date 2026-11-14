import sys


if len(sys.argv) != 3:
    raise SystemExit("Usage: python3 solve.py NONCE EXPECTED")

nonce, expected = sys.argv[1:]
if any(len(value) != 12 or not value.isalpha() or not value.isupper()
       for value in (nonce, expected)):
    raise SystemExit("NONCE et EXPECTED doivent contenir 12 lettres A-Z")

n = [ord(letter) - 65 for letter in nonce]
output = [ord(letter) - 65 for letter in expected]
rotation = sum(n) % 12
mixed = [output[(index - rotation) % 12] for index in range(12)]

state = n[-1]
secret = []
for index, value in enumerate(mixed):
    secret.append(chr(65 + (value - n[index] - state - index) % 26))
    state = value

print("".join(secret))
