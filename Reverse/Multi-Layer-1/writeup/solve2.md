
cp /proc/{PID}/exe stage2

Here the trick is that the xored flag is in a function which is executed before the main and this function is also the one we read directly to get the value because the function writes over itself. So just reading the address wouldn't give you a value.

But following a bit the functions you easily find

xored flag is bytes_20F0 
xor key is bytes 2104
```
>>> import pwn
>>> xored_flag= [
...   25, 154, 85, 208, 33, 187, 120, 236, 119, 174, 
...   36, 179, 46, 243, 58, 228, 105, 177, 39, 227
... ]
>>> xor_key=[90, 195,  23, 158]
>>> pwn.xor(xored_flag,xor_key)
b'CYBN{xor-m3-t0-z3r0}'
```
