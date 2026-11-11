import socket
import time
import secrets

# ============================================================
# CONFIGURATION
# ============================================================

SOURCE_IP = "10.64.0.249"
BROADCAST_IP = "10.64.0.255"
DESTINATION_PORT = 2121

INTERVAL = 5

# Plage de ports sources dynamiques
SOURCE_PORT_MIN = 49152
SOURCE_PORT_MAX = 65534

USERNAME = "JohnNeuill"
PASSWORD = "Cyb3rNightist@n"

MESSAGES = [
    f"USER={USERNAME}",
    f"PASS={PASSWORD}"
]


# ============================================================
# CREATION D'UN NOUVEAU SOCKET AVEC UN NOUVEAU PORT SOURCE
# ============================================================

def create_socket(previous_port=None):

    # Première tentative : laisser le système choisir
    # automatiquement un port source éphémère.
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    try:
        sock.bind((SOURCE_IP, 0))
        source_port = sock.getsockname()[1]

        # Vérifier que le port est différent du précédent.
        if source_port != previous_port:
            return sock, source_port

        sock.close()

    except OSError:
        sock.close()
        raise

    # Si le système réattribue le même port, choisir
    # explicitement un autre port source disponible.
    for attempt in range(200):

        source_port = secrets.randbelow(
            SOURCE_PORT_MAX - SOURCE_PORT_MIN + 1
        ) + SOURCE_PORT_MIN

        if source_port == previous_port:
            continue

        candidate = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM
        )

        candidate.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_BROADCAST,
            1
        )

        try:
            candidate.bind((SOURCE_IP, source_port))
            return candidate, source_port

        except OSError:
            candidate.close()

    raise RuntimeError(
        "Impossible d'obtenir un nouveau port source disponible."
    )


# ============================================================
# BOUCLE PRINCIPALE
# ============================================================

def main():

    previous_port = None
    pair_number = 0

    print("Démarrage du générateur UDP")
    print(f"Source      : {SOURCE_IP}")
    print(f"Destination : {BROADCAST_IP}:{DESTINATION_PORT}")
    print("--------------------------------------------")

    while True:

        sock = None

        try:

            pair_number += 1

            # Création d'un nouveau socket pour ce binôme.
            sock, source_port = create_socket(previous_port)

            previous_port = source_port

            print(f"\n[BINOME #{pair_number}]")
            print(f"Nouveau port source : {source_port}")

            for index, message in enumerate(MESSAGES):

                sock.sendto(
                    message.encode("utf-8"),
                    (BROADCAST_IP, DESTINATION_PORT)
                )

                print(
                    f"[{index + 1}/2] UDP envoyé : "
                    f"{SOURCE_IP}:{source_port} -> "
                    f"{BROADCAST_IP}:{DESTINATION_PORT}"
                )

                if index < len(MESSAGES) - 1:
                    print(f"Attente de {INTERVAL} secondes...")
                    time.sleep(INTERVAL)

        except OSError as e:

            print(f"Erreur réseau : {e}")
            time.sleep(2)

        finally:

            # Fermeture systématique du socket après le binôme.
            if sock is not None:
                sock.close()
                print(
                    f"Socket fermé (port source {previous_port})"
                )


if __name__ == "__main__":
    try:
        main()

    except KeyboardInterrupt:
        print("\nArrêt du générateur UDP.")
