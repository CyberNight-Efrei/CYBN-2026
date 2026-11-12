import asyncio
import contextlib
import itertools
import math
import os
import random
import re
import time


FLAG = os.environ["DYNAMIC_FLAG"]

SOFTWARE_ID = b"\x01" + f"NZZ-BUS-2.12-{FLAG}*".encode("ascii")
SOFTWARE_PGN = b"\xDA\xFE\x00"
ENGINE = 0x00


def frame(can_id, data):
    return f"{can_id:08X}#{data.hex().upper()}\n".encode("ascii")


async def send(writer, lock, frames):
    async with lock:
        writer.write(b"".join(frame(can_id, data) for can_id, data in frames))
        await writer.drain()


def telemetry(kind, elapsed):
    phase = elapsed % 42
    if phase < 8:
        speed = phase * 1.5
    elif phase < 25:
        speed = 11.6 + 0.4 * math.sin(phase)
    elif phase < 33:
        speed = (33 - phase) * 1.5
    else:
        speed = 0

    if kind == "speed":
        raw = round(speed * 256)
        return 0x18FEF121, b"\xFF" + raw.to_bytes(2, "little") + b"\xFF" * 5
    if kind == "temperature":
        temperature = round(88 + math.sin(elapsed / 60))
        return 0x18FEEE00, bytes([temperature + 40]) + b"\xFF" * 7

    rpm = 680 + 55 * speed + (100 if phase < 8 else 0) + 16 * math.sin(elapsed * 2)
    raw = round(rpm * 8)
    return 0x0CF00400, b"\xFF" * 3 + raw.to_bytes(2, "little") + b"\xFF" * 3


async def broadcast_telemetry(writer, lock):
    start = time.monotonic()
    kinds = itertools.cycle(("engine", "speed", "engine", "temperature", "speed"))
    while True:
        await send(writer, lock, [telemetry(next(kinds), time.monotonic() - start)])
        await asyncio.sleep(random.uniform(0.3, 0.7))


def data_packets(destination):
    packets = []
    for number, offset in enumerate(range(0, len(SOFTWARE_ID), 7), 1):
        chunk = SOFTWARE_ID[offset:offset + 7].ljust(7, b"\xFF")
        packets.append((0x1CEB0000 | destination << 8 | ENGINE,
                        bytes([number]) + chunk))
    return packets


def control(destination, command, max_packets):
    size = len(SOFTWARE_ID)
    return (0x1CEC0000 | destination << 8 | ENGINE,
            bytes([command, size & 0xFF, size >> 8,
                   (size + 6) // 7, max_packets]) + SOFTWARE_PGN)


def parse(line):
    match = re.fullmatch(rb"([0-9A-Fa-f]{8})#([0-9A-Fa-f]{0,16})\r?\n", line)
    if not match:
        return None
    can_id = int(match[1], 16)
    if can_id > 0x1FFFFFFF or len(match[2]) % 2:
        return None
    return can_id, bytes.fromhex(match[2].decode("ascii"))


async def handle(reader, writer):
    lock = asyncio.Lock()
    stream = asyncio.create_task(broadcast_telemetry(writer, lock))
    pending = None
    try:
        while line := await reader.readline():
            parsed = parse(line)
            if parsed is None:
                continue
            can_id, data = parsed
            source = can_id & 0xFF
            destination = (can_id >> 8) & 0xFF
            pdu_format = (can_id >> 16) & 0xFF
            data_page = (can_id >> 24) & 0x03

            if (data_page == 0 and pdu_format == 0xEA
                    and destination in (ENGINE, 0xFF)
                    and source not in (ENGINE, 0xFE, 0xFF)
                    and data == SOFTWARE_PGN):
                packets = data_packets(destination if destination == 0xFF else source)
                if destination == 0xFF:
                    await send(writer, lock,
                               [control(0xFF, 0x20, 0xFF), *packets])
                    pending = None
                else:
                    await send(writer, lock,
                               [control(source, 0x10, len(packets))])
                    pending = (source, packets, 1, time.monotonic())

            elif (pending is not None and data_page == 0
                  and pdu_format == 0xEC and destination == ENGINE
                  and source == pending[0] and len(data) == 8
                  and data[0] == 0x11 and data[5:] == SOFTWARE_PGN
                  and time.monotonic() - pending[3] < 15):
                source, packets, next_number, _ = pending
                if data[1] and data[2] == next_number:
                    last = min(next_number - 1 + data[1], len(packets))
                    await send(writer, lock, packets[next_number - 1:last])
                    pending = ((source, packets, last + 1, time.monotonic())
                               if last < len(packets) else None)
    except (ConnectionError, ValueError):
        pass
    finally:
        stream.cancel()
        with contextlib.suppress(asyncio.CancelledError, ConnectionError):
            await stream
        writer.close()
        with contextlib.suppress(ConnectionError):
            await writer.wait_closed()


async def main():
    host = "0.0.0.0"
    port = int(os.getenv("PORT", "1337"))
    server = await asyncio.start_server(handle, host, port, limit=128)
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
