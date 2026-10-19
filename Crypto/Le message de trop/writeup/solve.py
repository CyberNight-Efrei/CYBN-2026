#!/usr/bin/env python3
import json
import math
import re
from pathlib import Path


def integer_root(value, exponent):
    low, high = 0, 1 << ((value.bit_length() + exponent - 1) // exponent + 1)
    while high - low > 1:
        middle = (low + high) // 2
        if middle**exponent <= value:
            low = middle
        else:
            high = middle
    return low


path = Path(__file__).resolve().parents[1] / "dist" / "messages.json"
with path.open(encoding="utf-8") as file:
    transmissions = json.load(file)["transmissions"]

targets = [item for item in transmissions if item["e"] == 7]
assert len(targets) == 7
moduli = [int(item["n"], 16) for item in targets]
product = math.prod(moduli)
power = sum(int(item["c"], 16) * (product // n) * pow(product // n, -1, n)
            for item, n in zip(targets, moduli)) % product

m = integer_root(power, 7)
assert m**7 == power
message = m.to_bytes((m.bit_length() + 7) // 8, "big").decode("ascii")
flag = re.search(r"CYBN\{[A-Za-z0-9_-]+\}", message).group()

print("Message :", message)
print("Flag    :", flag)
