import socket
import sys


host, port = sys.argv[1], int(sys.argv[2])


def recv_until(sock, marker):
    data = bytearray()
    while not data.endswith(marker):
        chunk = sock.recv(1)
        if not chunk:
            break
        data.extend(chunk)
    return data.decode("ascii")


with socket.create_connection((host, port), timeout=5) as sock:
    for _ in range(10):
        message = recv_until(sock, b"> ")
        word = message.splitlines()[-2]
        sock.sendall((word[::-1] + "\n").encode("ascii"))
    print(recv_until(sock, b"\n").strip())
