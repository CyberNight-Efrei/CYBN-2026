# Rolling Codes Writeup

https://github.com/avrdudes/avr-libc/blob/main/libc/stdlib/random.c

Le programme en C prouve que le bruteforce peut être réalisé très rapidement.

On remarque que pour deux codes consécutifs c0 et c1 non xorés, c1 = do_random(c0). De plus, pour deux codes x0 et x1 xorés avec la clef, x0 ^ x1 = c0 ^ k ^ c1 ^ k = c0 ^ c1, permettant un bruteforce de la clef en local à partir de deux codes.

Note : 
```sh
gcc -o crack crack.c
bluetoothctl
scan on
scan off
list
pair CC:DB:A7:2D:E0:6A
> pin 1234
python wu.py
```
