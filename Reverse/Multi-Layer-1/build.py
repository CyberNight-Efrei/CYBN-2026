#!/usr/bin/env python3
"""
build.py - builds the 4-stage layered reverse challenge.

How it works
------------
Each stage is a small C program. Stage N carries stage N+1 INSIDE itself,
encrypted with AES-256-GCM. The key is never stored: stage N derives it from
the player's correct answer, so only the right answer opens the next layer.

    stage1 [ stage2 [ stage3 [ stage4 [ flag ]]]]      (each [] = AES-256-GCM)

Because the key depends on the answer, the build runs in two passes:

  Pass 1 (forward)  : compile every stage in KEYGEN mode and run it with the
                      correct answer, to learn which key that answer produces.
  Pass 2 (backward) : starting from the flag, encrypt each layer with its key,
                      embed it in the previous stage, and compile for real.

Result: dist/stage1 is the only file to give to players.
Requires: gcc, libssl-dev, and `pip install cryptography`.
"""
import os
import resource
import shutil
import signal
import subprocess
import sys
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# ---------------------------------------------------------------------------
# Challenge settings - edit these to make your own challenge
# ---------------------------------------------------------------------------

FLAG = "CYBN{3NF1N_F1N1_AV3C_C3TT3_H1ST01R3}"

STAGE1_PASSPHRASE = "CYBN{35SY_P3ASY}"  # visible with `strings`

STAGE2_PASSWORD = "CYBN{xor-m3-t0-z3r0}"            # hidden behind a XOR
STAGE2_XOR_KEY = bytes([0x5A, 0xC3, 0x17, 0x9E])

STAGE3_SALT = 0xC0FFEE1234ABCDEF              # mixed with the (always-0) page-offset trick

STRIP_BINARIES = True                         # strip symbols (harder to read)

# Stage 4 derives its key from THIS machine's network interfaces (see
# stage4.c). Building the real, deployable challenge MUST happen on your
# own machine, not in a disposable sandbox: whatever machine runs
# `python3 build.py` is the one whose /sys/class/net/*/address values get
# sealed into the flag's encryption key. Building it anywhere else bakes in
# that other machine's hardware instead of yours, and the core dump you
# hand to players (taken on YOUR machine - see the README) will then not
# match the key the shipped binary needs.

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent
BUILD = ROOT / "build"  # intermediate files
DIST = ROOT / "dist"    # what you give to players


# ---------------------------------------------------------------------------
# Generated C headers
# ---------------------------------------------------------------------------

def c_array(name: str, data: bytes) -> str:
    """Render bytes as a C array: static const unsigned char NAME[] = {...};"""
    rows = [", ".join(f"0x{b:02x}" for b in data[i:i + 16]) for i in range(0, len(data), 16)]
    body = ",\n    ".join(rows)
    return f"static const unsigned char {name}[] = {{\n    {body}\n}};\n"


def secrets_header(stage: int) -> str:
    """Per-stage constants that the C source needs (secrets.h)."""
    if stage == 1:
        return f'#define HIDDEN_PASSPHRASE "{STAGE1_PASSPHRASE}"\n'

    if stage == 2:
        pw = STAGE2_PASSWORD.encode()
        masked = bytes(b ^ STAGE2_XOR_KEY[i % len(STAGE2_XOR_KEY)] for i, b in enumerate(pw))
        return (f"#define PASSWORD_LEN {len(pw)}\n"
                + c_array("XOR_KEY", STAGE2_XOR_KEY)
                + c_array("PASSWORD_XOR", masked))

    if stage == 3:
        return f"#define STAGE3_SALT 0x{STAGE3_SALT:x}ULL\n"

    return ""  # stage 4 needs no compiled-in secret: see stage4.c


def write_headers(stage: int, next_blob: bytes) -> Path:
    """Write secrets.h and next_blob.h for one stage, return its build dir."""
    d = BUILD / f"stage{stage}"
    d.mkdir(parents=True, exist_ok=True)
    (d / "secrets.h").write_text(secrets_header(stage))
    (d / "next_blob.h").write_text(c_array("NEXT_BLOB", next_blob))
    return d


# ---------------------------------------------------------------------------
# Compiling and encrypting
# ---------------------------------------------------------------------------

def compile_stage(stage: int, output: Path, keygen: bool = False) -> None:
    cmd = ["gcc", "-O2", "-Wall", "-Wextra",
           "-I", str(ROOT), "-I", str(BUILD / f"stage{stage}"),
           "-o", str(output), str(ROOT / f"stage{stage}.c"), "-lcrypto"]
    if keygen:
        cmd.insert(1, "-DKEYGEN")
    if STRIP_BINARIES and not keygen:
        cmd.insert(1, "-s")
    if stage == 4:
        # Fixed load address, same on every run: see the file header in
        # stage4.c for why this is what makes a core dump of it useful.
        cmd.insert(1, "-no-pie")
    subprocess.run(cmd, check=True)


def encrypt(key: bytes, plaintext: bytes) -> bytes:
    """Blob = IV (12) || ciphertext || GCM tag (16), as read by common.h."""
    iv = os.urandom(12)
    return iv + AESGCM(key).encrypt(iv, plaintext, None)


# ---------------------------------------------------------------------------
# Pass 1: ask each stage which key its correct answer leads to
# ---------------------------------------------------------------------------

def keygen(stage: int, answer: str = "") -> tuple[bytes, str]:
    """Returns (key, stderr). `answer` is typed on stdin like a player would."""
    write_headers(stage, next_blob=bytes(1))  # placeholder, KEYGEN never uses it
    exe = BUILD / f"stage{stage}" / "keygen"
    compile_stage(stage, exe, keygen=True)

    # Every stage requires argc >= 2 (it's normally the previous stage's key,
    # see common.h/exec_from_memory); stage 3 no longer reads argv[1] for
    # anything (its problem comes from the page-offset trick instead), so
    # any placeholder value satisfies the check.
    run = subprocess.run([str(exe), "0" * 64], input=answer + "\n",
                         capture_output=True, text=True, check=True)
    key_hex = run.stdout.strip()[-64:]  # the key is the last thing printed (32 bytes = 64 hex chars)
    return bytes.fromhex(key_hex), run.stderr


# ---------------------------------------------------------------------------
# End-to-end check
# ---------------------------------------------------------------------------

def run_chain(answers: list[str]) -> subprocess.CompletedProcess:
    def no_core_dump():
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))

    return subprocess.run([str(DIST / "stage1")], input="\n".join(answers) + "\n",
                          capture_output=True, text=True, timeout=60,
                          preexec_fn=no_core_dump)


def verify(answers: list[str]) -> None:
    good = run_chain(answers)
    # Stage 4 aborts on purpose once it has unsealed the flag (see stage4.c).
    assert good.returncode == -signal.SIGABRT and "unsealed" in good.stdout, \
        f"full chain failed:\n{good.stdout}\n{good.stderr}"

    bad = run_chain(["wrong-passphrase"])
    assert "stays encrypted" in bad.stdout, "wrong passphrase was not rejected"
    print("verify: full chain opens with the right answers, refuses wrong ones")


# ---------------------------------------------------------------------------
# Stage 4's core dump: generated on THIS machine, for THIS machine's
# network-interface fingerprint (see stage4.c). Must be re-run whenever the
# challenge is rebuilt on a different machine.
# ---------------------------------------------------------------------------

def generate_coredump(answers: list[str]) -> Path | None:
    """Runs the full chain with core dumps enabled; on success, moves the
    resulting core file to dist/stage4.core and returns its path. Returns
    None (with a printed explanation) if this machine's core_pattern needs
    a manual step instead - see the README."""
    pattern = Path("/proc/sys/kernel/core_pattern").read_text().strip()

    if pattern.startswith("|"):
        print(f"skipped: core_pattern is piped to a handler ({pattern!r}) - "
              "this looks like systemd-coredump (or apport), common on desktop "
              "distros. Run the chain yourself, then either:\n"
              "    coredumpctl dump <pid-or-match> -o dist/stage4.core\n"
              "  or temporarily:\n"
              "    echo core | sudo tee /proc/sys/kernel/core_pattern\n"
              "    (rerun this script)\n"
              "    sudo sysctl -p   # or reboot, to restore the previous setting")
        return None

    run_dir = BUILD / "coredump_run"
    shutil.rmtree(run_dir, ignore_errors=True)
    run_dir.mkdir(parents=True)

    def enable_core_dump():
        resource.setrlimit(resource.RLIMIT_CORE,
                           (resource.RLIM_INFINITY, resource.RLIM_INFINITY))

    before = set(run_dir.iterdir())
    proc = subprocess.run([str((DIST / "stage1").resolve())],
                          input="\n".join(answers) + "\n",
                          capture_output=True, text=True, timeout=60,
                          cwd=run_dir, preexec_fn=enable_core_dump)
    new_files = set(run_dir.iterdir()) - before

    if proc.returncode != -signal.SIGABRT:
        print(f"skipped: the chain did not abort as expected (code {proc.returncode}); "
              f"no core dump produced.\n{proc.stdout}\n{proc.stderr}")
        shutil.rmtree(run_dir, ignore_errors=True)
        return None

    if not new_files:
        if pattern.startswith("/"):
            print(f"skipped: core_pattern is an absolute path ({pattern!r}) - the "
                  "core dump was written there, not next to dist/stage1. Find it "
                  "there (substituting any %p with this run's pid) and copy it to "
                  "dist/stage4.core yourself.")
        else:
            print(f"skipped: no core dump file appeared (core_pattern={pattern!r}). "
                  "Check `ulimit -c`, and that this filesystem allows core dumps.")
        shutil.rmtree(run_dir, ignore_errors=True)
        return None

    dest = DIST / "stage4.core"
    shutil.move(str(new_files.pop()), str(dest))
    shutil.rmtree(run_dir, ignore_errors=True)
    return dest


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    shutil.rmtree(BUILD, ignore_errors=True)
    DIST.mkdir(exist_ok=True)

    # Pass 1 - forward: which key does each correct answer produce?
    keys, plan_text = {}, ""
    keys[1], _ = keygen(1, answer=STAGE1_PASSPHRASE)
    keys[2], _ = keygen(2, answer=STAGE2_PASSWORD)
    keys[3], err = keygen(3)  # seeded by the (always-0) page-offset trick, see stage3.c
    keys[4], _ = keygen(4)
    plan_text = err.split(": ", 1)[1].strip().rstrip(",")  # e.g. "A1B1-10,A1B2-30"

    # Pass 2 - backward: wrap the flag, then each stage, in its own AES layer.
    payload = FLAG.encode()
    for stage in (4, 3, 2, 1):
        blob = encrypt(keys[stage], payload)
        write_headers(stage, next_blob=blob)
        exe = BUILD / f"stage{stage}" / "stage"
        compile_stage(stage, exe)
        payload = exe.read_bytes()  # this whole binary is the next layer's content

    shutil.copy(BUILD / "stage1" / "stage", DIST / "stage1")

    answers = [STAGE1_PASSPHRASE, STAGE2_PASSWORD, plan_text]
    verify(answers)

    core_path = generate_coredump(answers)

    answerstage3 = "CYBN{W4S_TR4NSP0RT_0PT1M1S5T10N_FUN}"
    (BUILD / "solution.txt").write_text(
        f"Stage 1 passphrase : {answers[0]}\n"
        f"Stage 2 password   : {answers[1]}\n"
        f"Stage 3 plan       : FLAG = {answerstage3}, PLAN = {answers[2]}\n"
        f"Flag               : {FLAG}\n")

    if core_path:
        print(f"done: give players {DIST / 'stage1'} AND {core_path}  "
              f"(answers in {BUILD / 'solution.txt'})")
    else:
        print(f"done: give players {DIST / 'stage1'} (answers in {BUILD / 'solution.txt'}); "
              f"see above for how to produce dist/stage4.core on this machine")


if __name__ == "__main__":
    sys.exit(main())
