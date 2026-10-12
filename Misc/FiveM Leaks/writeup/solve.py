import re, sys, os

root = sys.argv[1] if len(sys.argv) > 1 else "city_guard"
read = lambda p: open(os.path.join(root, p), encoding="utf-8").read()

man = read("fxmanifest.lua")
# config.lua s'exécute une fois par bloc où il est listé qui tourne côté serveur :
# shared_scripts (tourne aussi sur le serveur) + server_scripts => chargé 2 fois.
def in_block(block):
    m = re.search(block + r"\s*\{([^}]*)\}", man, re.S)
    return bool(m and "config.lua" in m.group(1))
loads = in_block("shared_scripts") + in_block("server_scripts")

# Fragment accumulé par config.lua à chaque chargement
cfg = re.search(r"Config\.FlagPrefix\s*=\s*\(Config\.FlagPrefix or ''\)\s*\.\.\s*'([^']*)'", read("config.lua")).group(1)

# Flux : UI (index.html) -> client.lua -> server.lua
A = re.search(r"body:\s*JSON\.stringify\(\{\s*s:\s*'([^']*)'", read("html/index.html")).group(1)
B = re.search(r"'city_guard:sync',\s*\(data\.s or ''\)\s*\.\.\s*'([^']*)'", read("client.lua")).group(1)

srv = read("server.lua")
# Préfixe littéral posé par server.lua
C = re.search(r"_state\.op\s*=\s*'([^']*)'\s*\.\.", srv).group(1)

# Le préfixe 'verb' vient d'un swizzle luaglm : vec4(...).<lettres> puis string.char
comps = [int(x, 16) for x in re.search(r"vec4\(([^)]*)\)", srv).group(1).split(",")]
sw = re.search(r"\.([xyzw]{2,4})", srv).group(1)
I = {"x": 0, "y": 1, "z": 2, "w": 3}
verb = bytes(comps[I[c]] for c in sw).decode()

# GetGameName() : native FiveM = "fxserver" côté serveur (cf. doc)
GAME = "fxserver"

# `fivem` : sucre CfxLua pour joaat("fivem")
def joaat(w):
    w = w.lower(); h = 0
    for c in w.encode():
        h = (h + c) & 0xffffffff; h = (h + (h << 10)) & 0xffffffff; h ^= h >> 6
    h = (h + (h << 3)) & 0xffffffff; h ^= h >> 11; h = (h + (h << 15)) & 0xffffffff
    return h
word = re.search(r"format\(`([^`]+)`\)", srv).group(1)
HASH = "%x" % joaat(word)

print(C + verb + cfg * loads + A + B + GAME + "_" + HASH + "}")
