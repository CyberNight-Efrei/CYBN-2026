#!/usr/bin/env python3

import sys, code, os, linecache, _imp

[__import__(_m) for _m in (
    "types functools itertools operator collections string textwrap "
    "base64 binascii struct json re math random datetime hashlib "
    "copy pprint dis opcode traceback warnings codecs _suggestions difflib "
    "encodings.ascii encodings.latin_1 "
    "_interpreters").split()]

linecache.getlines = lambda *a, **k: []
linecache.getline = lambda *a, **k: ""
linecache.checkcache = lambda *a, **k: None

import _signal
_signal.signal(_signal.SIGINT, _signal.SIG_IGN)

del _signal, sys.modules["_signal"]
del _imp.create_builtin
del _imp, sys.modules["_imp"]

import builtins as _b
for _n in ("license", "credits", "copyright"):
    setattr(_b, _n, "<disabled in this sandbox>")
del _b, _n

_POLICY = r'''
def _arm(_WRITE, _FLUSH, _EXIT, _LOADED):
    _BLOCKED = (
        "os.system", "os.exec", "os.posix_spawn", "os.spawn", "os.fork", "os.kill",
        "os.startfile", "subprocess.", "_posixsubprocess.", "pty.",

        "open", "os.remove", "os.unlink", "os.rename", "os.replace", "os.truncate",
        "os.mkdir", "os.rmdir", "os.chdir", "os.fchdir", "os.chmod", "os.chown",
        "os.utime", "os.link", "os.symlink", "os.listdir", "os.scandir",
        "shutil.", "tempfile.", "glob.", "sqlite3.",

        "socket.", "urllib.", "http.client", "ftplib.", "smtplib.", "imaplib.",
        "poplib.", "nntplib.", "webbrowser.",

        "ctypes.", "mmap.", "code.__new__", "pickle.find_class",
        "winreg.", "msvcrt.", "gc.",

        "sys._getframe", "sys._current_frames", "sys.settrace", "sys.setprofile",
        "sys.monitoring", "sys.remote_exec", "_thread.", "builtins.breakpoint",

        "os.putenv", "os.unsetenv",
    )

    def hook(event, args, _B=_BLOCKED, _WRITE=_WRITE, _FLUSH=_FLUSH, _EXIT=_EXIT,
             _LOADED=_LOADED):
        try:
            if event == "open" and args[1] == "rb":
                _path = str(args[0])
                if _path[:1] == "<" and _path[-1:] == ">":
                    return

            if event == "import" and args[0] not in _LOADED:
                _WRITE("\n[sandbox] denied: import %s -- session terminated\n" % (args[0],))
                _FLUSH()
                _EXIT(1)

            if event.startswith(_B) and event != "sys._getframemodulename":
                _WRITE("\n[sandbox] denied: %s -- session terminated\n" % event)
                _FLUSH()
                _EXIT(1)
        except BaseException:
            _EXIT(1)

    return hook
'''


def _build():
    ns = {}
    exec(_POLICY, ns)
    return ns.pop("_arm")(sys.stderr.write, sys.stderr.flush, os._exit, sys.modules)


_banner = f"Python {sys.version} (sandbox)"
_con = code.InteractiveConsole(locals={"__name__": "__sandbox__"})

sys.addaudithook(_build())

del _build, _POLICY

_con.interact(banner=_banner, exitmsg="")
