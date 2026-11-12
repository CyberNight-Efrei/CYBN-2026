import itertools
import socket
import sys

import zxingcpp
from PIL import Image, ImageOps


GLYPHS = {" ": (0, 0), "▀": (1, 0), "▄": (0, 1), "█": (1, 1)}
PROMPT = b"Mot de passe du coffre ? "


def receive_until(sock, marker):
    data = bytearray()
    while marker not in data:
        chunk = sock.recv(65536)
        if not chunk:
            break
        data.extend(chunk)
    return bytes(data)


def parse_pieces(message):
    text = message.decode("utf-8")
    print(text)
    pieces = []
    for block in text.split("\n\n"):
        block = block.lstrip("\n")
        if not block.startswith("Morceau "):
            continue
        rows = block.split("\n")[1:]
        if len(rows) != 11 or any(len(row) != 21 for row in rows):
            raise ValueError("Morceau incomplet")
        piece = []
        for row in rows:
            upper, lower = zip(*(GLYPHS[char] for char in row))
            piece.extend((list(upper), list(lower)))
        if any(piece[-1]):
            raise ValueError("Dernière demi-ligne invalide")
        piece.pop()
        pieces.append(piece)
    if len(pieces) != 4:
        raise ValueError("Quatre morceaux attendus")
    return pieces


def rotate(piece):
    return [list(row) for row in zip(*piece[::-1])]


def assemble(pieces):
    rotations = []
    for piece in pieces:
        variants = [piece]
        for _ in range(3):
            variants.append(rotate(variants[-1]))
        rotations.append(variants)

    for order in itertools.permutations(range(4)):
        for angles in itertools.product(range(4), repeat=4):
            tl, tr, bl, br = (rotations[index][angle] for index, angle in zip(order, angles))
            if any(a[-1] != b[0] for a, b in zip(tl, tr)):
                continue
            if any(a[-1] != b[0] for a, b in zip(bl, br)):
                continue
            if tl[-1] != bl[0] or tr[-1] != br[0]:
                continue
            matrix = [a + b for a, b in zip(tl, tr)] + [a + b for a, b in zip(bl, br)]
            image = Image.new("L", (42, 42), 255)
            image.putdata([0 if bit else 255 for row in matrix for bit in row])
            image = ImageOps.expand(image, border=8, fill=255)
            result = zxingcpp.read_barcode(image.resize((232, 232), Image.Resampling.NEAREST))
            if result and result.format == zxingcpp.BarcodeFormat.QRCode:
                return result.text
    raise ValueError("Aucun QR décodable")


def main(host, port):
    with socket.create_connection((host, port), timeout=10) as sock:
        sock.settimeout(10)
        print(receive_until(sock, b"> ").decode("utf-8"), end="")
        sock.sendall(b"\n")
        while True:
            message = receive_until(sock, PROMPT)
            if PROMPT not in message:
                print(message.decode("utf-8"), end="")
                return
            word = assemble(parse_pieces(message))
            print(f"Mot trouvé : {word}")
            sock.sendall((word + "\n").encode("ascii"))


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]))
