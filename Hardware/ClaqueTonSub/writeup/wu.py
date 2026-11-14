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