import socket
import time

# Configuration
BROADCAST_IP = "10.64.1.255"
PORT = 2121
INTERVAL = 5

MESSAGES = [
    "USER=JohnNeuill",
    "PASS=Cyb3rNightist@n"
]

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    while True:
        try:
            for i, message in enumerate(MESSAGES):
                sock.sendto(message.encode("utf-8"), (BROADCAST_IP, PORT))
                print(f"[{i + 1}/{len(MESSAGES)}] Envoy      {BROADCAST_IP}:{PORT} : {message}")

                if i < len(MESSAGES) - 1:
                    print(f"Attente de {INTERVAL} secondes...")
                    time.sleep(INTERVAL)
        except Excption as e:
            print("Lol une erreur : ", e)

if __name__ == "__main__":
    main()