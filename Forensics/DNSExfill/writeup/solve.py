"""Reconstruit la note à partir du PCAP distribué."""

import base64
from pathlib import Path

from scapy.all import DNS, rdpcap


capture = Path(__file__).resolve().parents[1] / "public" / "capture.pcap"
blocks = {}

for packet in rdpcap(str(capture)):
    if DNS not in packet or packet[DNS].qr != 0:
        continue
    name = packet[DNS].qd.qname.decode("ascii").rstrip(".")
    if not name.endswith(".evil.cybn.fr"):
        continue
    number, block, _ = name.split(".", 2)
    blocks[int(number)] = block

if not blocks or sorted(blocks) != list(range(len(blocks))):
    raise SystemExit("Blocs DNS absents ou incomplets.")

encoded = "".join(blocks[number] for number in sorted(blocks))
note = base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4))
print(note.decode("utf-8"))
