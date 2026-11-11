#!/usr/bin/env python3
"""Hide text inside a .wav using the Collatz conjecture.

The text is turned into a Collatz seed and the seed's sequence is played one
note per term. Even terms (n -> n/2) are short notes, odd terms (n -> 3n+1)
are long notes, so the rhythm is the parity sequence -- and the parity
sequence uniquely identifies the seed. Pitch (term mod 20 on a pentatonic
scale) is decoration / a hint.

    python3 create.py 'CYBERNIGHT{...}' -o chall.wav             # whole text = one seed
    python3 create.py 'CYBERNIGHT{...}' --per-char -o chall.wav  # one seed per byte
"""

import argparse
import wave

import numpy as np

SAMPLE_RATE = 44100
PENTATONIC = [0, 3, 5, 7, 10]


def collatz(n):
    """Yield the Collatz sequence starting at n, ending at 1."""
    if n < 1:
        raise ValueError("seed must be >= 1")
    while n != 1:
        yield n
        n = n // 2 if n % 2 == 0 else 3 * n + 1
    yield 1


def to_midi(value, root=48, octaves=4, scale=PENTATONIC):
    steps = len(scale) * octaves
    i = value % steps
    return root + 12 * (i // len(scale)) + scale[i % len(scale)]


def midi_to_freq(note):
    return 440.0 * 2.0 ** ((note - 69) / 12.0)


def render_note(freq, duration, amplitude=0.35, attack=0.01, release=0.15):
    """Sine + two quieter harmonics with an attack/release envelope."""
    n = int(SAMPLE_RATE * duration)
    i = np.arange(n)
    t = 2 * np.pi * freq * i / SAMPLE_RATE
    s = np.sin(t) + 0.3 * np.sin(2 * t) + 0.12 * np.sin(3 * t)
    a = max(1, int(n * attack))
    r = max(1, int(n * release))
    env = np.ones(n)
    env[:a] = i[:a] / a
    tail = i > n - r
    env[tail] = (n - i[tail]) / r
    return amplitude * env * s / 1.42


def render_sequence(seed, short, long_, gap):
    silence = np.zeros(int(SAMPLE_RATE * gap))
    parts = []
    for value in collatz(seed):
        duration = short if value % 2 == 0 else long_
        parts.append(render_note(midi_to_freq(to_midi(value)), duration))
        parts.append(silence)
    return parts


def write_wav(path, samples):
    pcm = (np.clip(samples, -1.0, 1.0) * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        w.writeframes(pcm.tobytes())


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("text", help="text / flag to hide")
    p.add_argument("-o", "--output", default="chall.wav")
    p.add_argument("--per-char", action="store_true",
                   help="one Collatz sequence per byte (easier) instead of one big seed")
    p.add_argument("--short", type=float, default=0.08, help="even-step note length (s)")
    p.add_argument("--long", type=float, default=0.16, help="odd-step note length (s)")
    p.add_argument("--gap", type=float, default=0.015, help="silence between notes (s)")
    p.add_argument("--char-gap", type=float, default=0.6,
                   help="silence between characters in --per-char mode (s)")
    args = p.parse_args()

    data = args.text.encode()
    if args.per_char:
        if 0 in data:
            p.error("NUL bytes can't be encoded (seed must be >= 1)")
        seeds = list(data)
    else:
        seeds = [int.from_bytes(data, "big")]

    parts, notes = [], 0
    for k, seed in enumerate(seeds):
        if k:
            parts.append(np.zeros(int(SAMPLE_RATE * args.char_gap)))
        seq = render_sequence(seed, args.short, args.long, args.gap)
        notes += len(seq) // 2
        parts.extend(seq)

    samples = np.concatenate(parts)
    write_wav(args.output, samples)
    mode = "per-char" if args.per_char else "big-int"
    print(f"{len(data)} bytes, {mode}: {notes} notes -> {args.output} "
          f"({len(samples) / SAMPLE_RATE:.1f}s)")


if __name__ == "__main__":
    main()
