import socket


HOST = "A_COMPLETER"
PORT = 0  # A_COMPLETER


def recv_until(sock, marker):
    data = bytearray()
    while not data.endswith(marker):
        chunk = sock.recv(1)
        if not chunk:
            break
        data.extend(chunk)
    return data.decode("ascii")


def main():
    with socket.create_connection((HOST, PORT), timeout=5) as sock:
        for _ in range(10):
            message = recv_until(sock, b"> ")
            print(message, end="")
            if not message.endswith("> "):
                return
            word = message.splitlines()[-2]
            # Exemple d'envoi : sock.sendall(b"reponse\n")
            # Exemple de lecture : sock.recv(1024)
            # A toi de repondre au robot avant le mot suivant.
        print(recv_until(sock, b"\n"), end="")


if __name__ == "__main__":
    main()
