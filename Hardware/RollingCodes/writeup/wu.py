import socket
import time
import subprocess
import sys

RANDOM_MAX = 0x7FFFFFFF

found = False

MAC = 'cc:db:a7:2d:e0:6a'

def code(x):
    if x == 0:
        x = 123459876
    hi = x // 127773
    lo = x % 127773
    x = 16807 * lo - 2836 * hi
    if x < 0:
        x += 0x7FFFFFFF
    rand = x % (RANDOM_MAX + 1)
    return rand

def try_key(k):
    global found
    s = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
    s.connect((MAC, 1))
    x = s.recv(4)
    x = x[::-1] # Little endian: we reverse the bytes
    print("recieved ", x.hex())
    c = code(int.from_bytes(x) ^ k) ^ k
    print("sending", hex(c))
    s.sendall(c.to_bytes(4, byteorder='little'))
    x = s.recv(1024).decode()
    print(x)
    if x != 'ok':
        s.close
        return

    found = True
    s.sendall(b"UNLOCK")
    x = s.recv(1024).decode()
    print(x)
    s.close()

def get_code():
    s = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
    s.connect((MAC, 1))
    x = s.recv(4)
    s.close()
    return int.from_bytes(x, byteorder='little')

def bruteforce(x0, x1):
    proc = subprocess.Popen(
        ["./crack", str(x0), str(x1)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )

    for line in proc.stdout:
        try_key(int(line))
        if found:
            sys.exit(0)

def chall():
    x0 = get_code()
    time.sleep(0.5)
    x1 = get_code()
    bruteforce(x0, x1)

chall()
