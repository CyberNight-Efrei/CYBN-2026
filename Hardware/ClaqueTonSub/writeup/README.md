# Claque Ton Sub

1ere étape : recon

On à affaire à du Bluetooth Low Energy. Avec nRF Connect sur téléphone, on peut se connecter à l'ESP32 pour énumérer les services présents.

On remarque un service inconnu (avec la handle 0x7fff00) composé de deux caractéristiques : une en NOTIFY, et une en WRITE.

En s'abonnant au NOTIFY, et en écrivant 32 bits à 0 sur le WRITE, on reçoit 16 bytes de données, dont la représentation en ASCII contient "JFIF". Il s'agit donc du début d'un fichier JPEG.

Il est écrit dans l'énoncé que l'ESP32 est en little-endian sur 32 bits. Si on écrit 1 avec ces paramètres, on reçoit la suite de l'image.

2eme étape : scripting

Plus qu'à passer sur un PC et écrire un script pour récupérer l'entièreté de l'image, à l'aide de la librairie Python Bleak.

```py
# Merci ThaySan

import asyncio
from bleak import BleakClient


img = b""
i = 0
running = False
out_img = open('./flag.jpg', 'wb')

async def main():
    global running
    
    ble_address = "8C:94:DF:68:1B:F2"
    char_notify = "7fff0002-0000-4000-8000-000000000000"
    char_write  = "7fff0001-0000-4000-8000-000000000000"

    async with BleakClient(ble_address) as client:
        async def handler(char, data):
            global img, i, running, out_img
            if b"Index is not valid" in data:
                running = False
                return
            print(f"Received: {data}")
            img += data
            out_img.write(data)
            i += 1
            await client.write_gatt_char(char_write, i.to_bytes(4, 'little'))
            
        running = True
        await client.start_notify(char_notify, handler)
        while running:
            await asyncio.sleep(0.1)
        await client.stop_notify(char_notify)
        out_img.close()

asyncio.run(main())
```

Et hop, sur l'image est affiché le flag
