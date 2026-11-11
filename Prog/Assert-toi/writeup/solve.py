import socket
import sys

SOLUTIONS = [
    # 1. __add
    'x = setmetatable({}, {__add = function() return 1337 end})',
    # 2. __index
    'x = setmetatable({}, {__index = function() return "CYBN" end})',
    # 3. __len
    'x = setmetatable({}, {__len = function() return 1337 end})',
    # 4. __call avec état
    'local n = 0\nx = setmetatable({}, {__call = function() n = n + 1 return n end})',
    # 5. NaN
    'x = 0/0',
    # 6. __lt / __le
    'x = setmetatable({}, {__lt = function() return true end, __le = function() return false end})',
    # 7. __eq + __add
    'local mt = {}\nmt.__eq = function() return true end\nmt.__add = function() return setmetatable({}, mt) end\nx = setmetatable({}, mt)',
    # 8. __newindex / __index vers une table cachée
    'local store = {}\nlocal swap = {a = "b", b = "a"}\n'
    'x = setmetatable({}, {\n'
    '  __newindex = function(_, k, v) store[swap[k] or k] = v end,\n'
    '  __index = store,\n'
    '})',
    # 9. __tostring, __concat, __metatable
    'x = setmetatable({}, {\n'
    '  __tostring = function() return "CYBN" end,\n'
    '  __concat = function(a, b) return tostring(a) .. tostring(b) end,\n'
    '  __metatable = "touche pas",\n'
    '})',
    # 10. __call comme itérateur
    'local vals = {1000, 300, 37}\n'
    'local i = 0\n'
    'x = setmetatable({}, {__call = function() i = i + 1 return vals[i] end})',
    # 11. __close
    'x = setmetatable({}, {__close = function(self) self.closed = (self.closed or 0) + 1 end})',
]


def read_until(f, marker):
    buf = ""
    while marker not in buf:
        c = f.read(1)
        if not c:
            break
        buf += c
    return buf


def solve(f):
    for i, code in enumerate(SOLUTIONS, 1):
        read_until(f, "\n> ")
        f.write(code + "\nEOF\n")
        f.flush()
        res = f.readline()
        print(f"[{i:2}] {res.strip()}")
        if "Raté" in res:
            sys.exit(1)
    print(f.read())


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    host = sys.argv[1] if len(sys.argv) > 1 else "localhost"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 5002
    s = socket.create_connection((host, port))
    solve(s.makefile("rw", encoding="utf-8", newline="\n"))
