import asyncio
import os
import secrets
import time
from pathlib import Path

import qrcode


HOST = "0.0.0.0"
PORT = 1337
DEADLINE = 3.0
FLAG = os.environ["DYNAMIC_FLAG"]
WORDS = Path(__file__).with_name("words.txt").read_text(encoding="utf-8").splitlines()
assert WORDS and len(WORDS) == len(set(WORDS))
assert all(word.isascii() and word.isalpha() and word.islower() and len(word) <= 17 for word in WORDS)
INTRO_LOCK = asyncio.Lock()
LAST_INTRO = 0.0


def make_qr(word):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=1,
        border=0,
    )
    qr.add_data(word)
    qr.make(fit=False)
    matrix = qr.get_matrix()

    # La marge blanche n'est ajoutée qu'au QR complet affiché après un échec.
    return [[bit for bit in row for _ in range(2)] for row in matrix for _ in range(2)]


def with_quiet_zone(matrix):
    white = [False] * (len(matrix) + 16)
    return [white[:] for _ in range(8)] + [([False] * 8) + row + ([False] * 8) for row in matrix] + [white[:] for _ in range(8)]


def rotate(piece):
    return [list(row) for row in zip(*piece[::-1])]


def cut_and_mix(matrix):
    half = len(matrix) // 2
    pieces = [
        [row[x : x + half] for row in matrix[y : y + half]]
        for y, x in ((0, 0), (0, half), (half, 0), (half, half))
    ]
    # Ramène le coin extérieur de chaque morceau en haut à gauche.
    for index, turns in enumerate((0, 3, 1, 2)):
        piece = pieces[index]
        for _ in range(turns):
            piece = rotate(piece)
        pieces[index] = piece
    secrets.SystemRandom().shuffle(pieces)
    return pieces


def render(matrix):
    glyphs = {(False, False): " ", (True, False): "▀", (False, True): "▄", (True, True): "█"}
    return "\n".join(
        "".join(glyphs[upper, lower] for upper, lower in zip(matrix[y], matrix[y + 1] if y + 1 < len(matrix) else [False] * len(matrix[y])))
        for y in range(0, len(matrix), 2)
    )


async def send(writer, message):
    writer.write(message.encode("utf-8"))
    await writer.drain()


async def read_line(reader, timeout):
    try:
        return await asyncio.wait_for(reader.readline(), timeout)
    except (asyncio.TimeoutError, ValueError):
        return b""


async def handle(reader, writer):
    global LAST_INTRO
    try:
        connected = time.monotonic()
        async with INTRO_LOCK:
            await asyncio.sleep(max(0, connected + 1 - time.monotonic(), LAST_INTRO + 1 - time.monotonic()))
            await send(
                writer,
                "Tu as intercepté le canal des braqueurs. Leur bot va transmettre les quatre morceaux du prochain QR.\n"
                "Appuie sur Entrée quand tu es prêt à lancer le hack.\n> ",
            )
            LAST_INTRO = time.monotonic()
        if not await read_line(reader, 60):
            return

        word = secrets.choice(WORDS)
        matrix = make_qr(word)
        pieces = cut_and_mix(matrix)
        blocks = "\n\n".join(
            f"Morceau {index}/4\n{render(piece)}" for index, piece in enumerate(pieces, 1)
        )
        await send(writer, f"\n{blocks}\n\nMot de passe du coffre ? ")

        started = time.monotonic()
        answer = await read_line(reader, DEADLINE)
        elapsed = time.monotonic() - started
        if not answer or elapsed > DEADLINE or answer.decode("utf-8", "replace").strip().lower() != word:
            await send(
                writer,
                f"\nPerdu. Ils ont ouvert le coffre avant toi.\n\nQR attendu :\n{render(with_quiet_zone(matrix))}\n"
                f"Mot de passe : {word}\n",
            )
            return

        await send(writer, f"\nLe coffre s'ouvre avant qu'ils ne comprennent. {FLAG}\n")
    except (BrokenPipeError, ConnectionResetError):
        pass
    finally:
        writer.close()
        try:
            await writer.wait_closed()
        except ConnectionError:
            pass


async def main():
    server = await asyncio.start_server(handle, HOST, PORT, limit=256)
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
