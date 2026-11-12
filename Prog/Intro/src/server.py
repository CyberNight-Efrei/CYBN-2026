import asyncio
import os
import secrets
import time
from pathlib import Path


HOST = "0.0.0.0"
PORT = 1337
ROUNDS = 10
TIME_LIMIT = 3.0
FLAG = os.environ["DYNAMIC_FLAG"]
WORDS = Path(__file__).with_name("words.txt").read_text(encoding="ascii").splitlines()
if not WORDS or not all(word.isascii() and word.isalpha() and word.islower() for word in WORDS):
    raise ValueError("words.txt doit contenir des mots minuscules ASCII")

BANNER = (
    b"  [ TOBOR // ACCUEIL DE NUIT ]\n"
    b"  ruojnoB... euh non, bonjour... Enfin je crois ?\n"
    b"  Depuis le patch de 03:00, je ne me sens pas tres nieb...\n"
    b"  Certains mots me semblent a l'envers.\n"
    b"  Aide-moi a les remettre a l'endroit. Tu as 3 sednoces !\n\n"
)


async def handle(reader, writer):
    try:
        writer.write(BANNER)
        await writer.drain()
        deadline = None

        for i in range(1, ROUNDS + 1):
            word = secrets.choice(WORDS)
            writer.write((f"{word[::-1]}\n[{i}/{ROUNDS}] > ").encode("ascii"))
            await writer.drain()
            if deadline is None:
                deadline = time.monotonic() + TIME_LIMIT

            try:
                answer = await asyncio.wait_for(reader.readline(), max(0, deadline - time.monotonic()))
            except asyncio.TimeoutError:
                writer.write(b"Tobor: Trop tard... je retourne en veille.\n")
                await writer.drain()
                return
            except ValueError:
                writer.write(b"Tobor: Reponse trop longue. Je retourne en veille.\n")
                await writer.drain()
                return

            if time.monotonic() > deadline:
                writer.write(b"Tobor: Trop tard... je retourne en veille.\n")
                await writer.drain()
                return
            if not answer:
                return
            if answer.rstrip(b"\r\n") != word.encode("ascii"):
                writer.write(b"Tobor: Mauvaise reponse. Je retourne en veille.\n")
                await writer.drain()
                return

        writer.write((f"Tobor: Bien joue ! {FLAG}\n").encode("ascii"))
        await writer.drain()
    except (BrokenPipeError, ConnectionResetError):
        pass
    finally:
        writer.close()
        try:
            await writer.wait_closed()
        except ConnectionError:
            pass


async def main():
    server = await asyncio.start_server(handle, HOST, PORT, limit=128)
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
