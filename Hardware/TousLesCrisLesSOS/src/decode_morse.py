
import serial
import time
import sys

PORT = ""
BAUD = 0

POINT = 0
TRAIT = 0
PAUSE_SYMBOLE = 0
PAUSE_LETTRE = 0

if PORT == "":
    print("Please set PORT (e.g COM0 or /dev/ttyUSB0)")
    sys.exit(1)

if BAUD == 0:
    print("Please set BAUD in bits per second (e.g 115200)")
    sys.exit(1)

if POINT == 0:
    print("Please set POINT in ms")
    sys.exit(1)

if TRAIT == 0:
    print("Please set TRAIT in ms")
    sys.exit(1)

if PAUSE_SYMBOLE == 0:
    print("Please set PAUSE_SYMBOLE in ms")
    sys.exit(1)

if PAUSE_LETTRE == 0:
    print("Please set PAUSE_LETTRE in ms")
    sys.exit(1)

SEUIL_HAUT = (POINT + TRAIT) / 2
SEUIL_BAS = (PAUSE_SYMBOLE + PAUSE_LETTRE) / 2

MORSE = {
    ".-": "A", "-...": "B", "-.-.": "C", "-..": "D",
    ".": "E", "..-.": "F", "--.": "G", "....": "H",
    "..": "I", ".---": "J", "-.-": "K", ".-..": "L",
    "--": "M", "-.": "N", "---": "O", ".--.": "P",
    "--.-": "Q", ".-.": "R", "...": "S", "-": "T",
    "..-": "U", "...-": "V", ".--": "W", "-..-": "X",
    "-.--": "Y", "--..": "Z",

    "-----": "0", ".----": "1", "..---": "2",
    "...--": "3", "....-": "4", ".....": "5",
    "-....": "6", "--...": "7", "---..": "8",
    "----.": "9",

    ".-.-.-": ".", "--..--": ",", "..--..": "?",
    ".----.": "'", "-.-.--": "!", "-..-.": "/",
    "-.--.": "(", "-.--.-": ")", ".-...": "&",
    "---...": ":", "-.-.-.": ";", "-...-": "=",
    ".-.-.": "+", "-....-": "-", "..--.-": "_",
    ".-..-.": '"', "...-..-": "$", ".--.-.": "@",
}

ser = serial.Serial(PORT, BAUD, timeout=0.01)

precedent = None
debut = time.monotonic()
lettre = ""
texte_commence = False
espace_envoye = False

def afficher_lettre():
    global lettre, texte_commence
    if lettre:
        print(MORSE.get(lettre, "?"), end="", flush=True)
        lettre = ""
        texte_commence = True

print("Décodage Morse :")

while True:
    data = ser.read(1)
    maintenant = time.monotonic()
    bit = int(data) if data in (b"0", b"1") else None

    if bit is not None:
        if precedent is None:
            precedent = bit
            debut = maintenant

        elif bit != precedent:
            duree = (maintenant - debut) * 1000

            if precedent == 1:
                lettre += "-" if duree >= SEUIL_HAUT else "."

            elif duree >= SEUIL_BAS:
                afficher_lettre()

            precedent = bit
            debut = maintenant

            if bit == 1:
                espace_envoye = False

    if precedent == 0:
        duree = (maintenant - debut) * 1000

        if duree >= SEUIL_BAS:
            afficher_lettre()

        if (duree >= 2 * PAUSE_LETTRE
                and texte_commence and not espace_envoye):
            print(" ", end="", flush=True)
            espace_envoye = True
