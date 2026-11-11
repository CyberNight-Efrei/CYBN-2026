import sys
import wave
import numpy as np

f = wave.open(sys.argv[1] if len(sys.argv) > 1 else "chall.wav")
rate = f.getframerate()
audio = np.frombuffer(f.readframes(f.getnframes()), dtype=np.int16)

# find the notes: anything louder than 1% of the max is "sound"
loud = np.abs(audio) > np.abs(audio).max() * 0.01
pos = np.where(loud)[0]

# a jump of more than 5ms between loud samples = silence between two notes
breaks = np.where(np.diff(pos) > rate * 0.005)[0]
starts = [pos[0]] + list(pos[breaks + 1])
ends = list(pos[breaks]) + [pos[-1]]

# short notes = even, long notes = odd
bits = []
for s, e in zip(starts, ends):
    duration = (e - s) / rate
    bits.append(1 if duration > 0.12 else 0)

print(len(bits), "notes")
print("".join(map(str, bits)))

# collatz backwards: 
# - last number is 1
# - even step: 
#   -> n came from 2n
# - odd step: 
#   -> n came from (n-1)/3
n = 1
for b in reversed(bits[:-1]):
    if b == 0:
        n = n * 2
    else:
        n = (n - 1) // 3

print(n)
print(n.to_bytes((n.bit_length() + 7) // 8, "big"))
