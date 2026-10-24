import socket
import sys


host, port = sys.argv[1], int(sys.argv[2])
with socket.create_connection((host, port), timeout=10) as connection:
    connection.settimeout(10)
    stream = connection.makefile("rb")
    connection.sendall(b"18EAFFFA#DAFE00\n")

    size = count = None
    parts = {}
    while True:
        line = stream.readline().strip()
        can_id, data = line.split(b"#", 1)
        payload = bytes.fromhex(data.decode("ascii"))

        if can_id == b"1CECFF00" and payload[0] == 0x20 and payload[5:] == b"\xDA\xFE\x00":
            size = int.from_bytes(payload[1:3], "little")
            count = payload[3]
            parts.clear()
        elif can_id == b"1CEBFF00" and size is not None:
            parts[payload[0]] = payload[1:]
            if len(parts) == count:
                message = b"".join(parts[number] for number in range(1, count + 1))[:size]
                print(message[1:].decode("ascii").rstrip("*"))
                break
