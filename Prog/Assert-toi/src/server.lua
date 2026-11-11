io.stdout:setvbuf("no")

local FLAG_PATH = os.getenv("FLAG_PATH") or "/app/flag.txt"
local MAX_CODE = 8192
local MAX_INSTR = 2000000
local HOOK_STEP = 1000

local f = assert(io.open(FLAG_PATH, "r"))
local FLAG = f:read("l")
f:close()

local _assert, _error, _pcall, _xpcall, _type, _tostring = assert, error, pcall, xpcall, type, tostring
local _load, _next, _pairs, _select = load, next, pairs, select
local write, read = io.write, io.read
local sethook, getinfo = debug.sethook, debug.getinfo

local function copy(t, skip)
  local c = {}
  for k, v in _pairs(t) do
    if not (skip and skip[k]) then c[k] = v end
  end
  return c
end

-- Les méthodes des chaînes passent par __index : sans ça, ("").dump atteindrait string.dump
local SAFE_STRING = copy(string, { dump = true })
local string_mt = getmetatable("")
string_mt.__index = SAFE_STRING
string_mt.__metatable = false

local EXHAUSTED = "trop d'instructions, on se calme"
local budget = 0
local run_level

-- Le hook est encore actif quelques instructions après le retour du pcall de run_level
local function hook()
  budget = budget - HOOK_STEP
  if budget <= 0 and getinfo(2, "f").func ~= run_level then
    _error(EXHAUSTED, 0)
  end
end

local function check_budget(...)
  if budget <= 0 then _error(EXHAUSTED, 0) end
  return ...
end

local function safe_pcall(...) return check_budget(_pcall(...)) end

-- Lever une erreur depuis le hook appelle le gestionnaire avec les hooks désactivés
local function safe_xpcall(fn, h, ...)
  if _type(h) ~= "function" then return check_budget(_xpcall(fn, h, ...)) end
  return check_budget(_xpcall(fn, function(e)
    if budget <= 0 then return e end
    return h(e)
  end, ...))
end

-- Un __gc s'exécuterait plus tard, hors du hook qui limite les instructions
local function safe_setmetatable(t, mt)
  if _type(mt) == "table" and rawget(mt, "__gc") ~= nil then
    _error("__gc n'est pas autorisé ici", 2)
  end
  return setmetatable(t, mt)
end

local function player_env()
  local env = {
    assert = assert, error = error, pcall = safe_pcall, xpcall = safe_xpcall,
    type = type, tostring = tostring, tonumber = tonumber, select = select,
    next = next, pairs = pairs, ipairs = ipairs,
    rawget = rawget, rawset = rawset, rawequal = rawequal, rawlen = rawlen,
    getmetatable = getmetatable, setmetatable = safe_setmetatable,
    string = copy(SAFE_STRING),
    table = copy(table), math = copy(math), utf8 = copy(utf8),
    print = function(...)
      local n = _select("#", ...)
      local parts = {}
      for i = 1, n do
        local v = _select(i, ...)
        local t = _type(v)
        if t == "string" then
          parts[i] = v
        elseif t == "number" or t == "boolean" or t == "nil" then
          parts[i] = _tostring(v)
        else
          parts[i] = "<" .. t .. ">"
        end
      end
      write("[print] ", table.concat(parts, "\t"), "\n")
    end,
  }
  env._G = env
  return env
end

local function check_env(x)
  return {
    x = x,
    assert = function(v, ...)
      if not v then _error("assertion failed!", 2) end
      return v, ...
    end,
    type = _type, tostring = _tostring, pcall = _pcall,
    next = _next, rawequal = rawequal, rawget = rawget, rawlen = rawlen,
    getmetatable = getmetatable, setmetatable = setmetatable,
  }
end

local LEVELS = {
  {
    name = "Échauffement",
    check = [[
assert(type(x) == "table")
assert(x + 1 == 1337)]],
  },
  {
    name = "Tout le monde s'appelle CYBN",
    check = [[
assert(type(x) == "table" and next(x) == nil)
assert(x.flag == "CYBN" and x[42] == "CYBN" and x[x] == "CYBN")]],
  },
  {
    name = "Le vide qui pèse lourd",
    check = [[
assert(type(x) == "table" and next(x) == nil)
assert(#x == 1337)]],
  },
  {
    name = "Compte jusqu'à trois",
    check = [[
assert(type(x) == "table")
assert(x() == 1 and x() == 2 and x() == 3)]],
  },
  {
    name = "Crise d'identité",
    check = [[
assert(x ~= x)]],
  },
  {
    name = "Ni plus, ni moins",
    check = [[
assert(type(x) == "table")
assert(x < 0 and x > 0)
assert(not (x <= 0) and not (x >= 0))]],
  },
  {
    name = "Un de plus, ça change rien",
    check = [[
assert(type(x) == "table")
assert(x == x + 1 and x + 1 == x + 2)
assert(not rawequal(x, x + 1))]],
  },
  {
    name = "Chassé-croisé",
    check = [[
assert(type(x) == "table")
x.a = 1
x.b = 2
assert(next(x) == nil)
assert(x.a == 2 and x.b == 1)]],
  },
  {
    name = "Déguisement",
    check = [[
assert(type(x) == "table")
assert(tostring(x) == "CYBN")
assert(x .. "!" == "CYBN!" and "!" .. x == "!CYBN")
assert(getmetatable(x) == "touche pas")
assert(not pcall(setmetatable, x, nil))]],
  },
  {
    name = "Boucle infinie (ou presque)",
    check = [[
assert(type(x) == "table" and next(x) == nil)
local s = 0
for v in x do s = s + v end
assert(s == 1337)]],
  },
  {
    name = "Ferme la porte en sortant",
    check = [[
assert(type(x) == "table")
for i = 1, 3 do
  local door <close> = x
end
assert(x.closed == 3)]],
  },
}

local function errmsg(e)
  if _type(e) == "string" then return e end
  return "erreur de type " .. _type(e)
end

local function read_code()
  local lines, size = {}, 0
  while true do
    local line = read("l")
    if line == nil then return nil end
    line = line:gsub("\r$", "")
    if line == "EOF" then break end
    size = size + #line + 1
    if size <= MAX_CODE then lines[#lines + 1] = line end
  end
  if size > MAX_CODE then return false end
  return table.concat(lines, "\n")
end

function run_level(lvl)
  local code = read_code()
  if code == nil then os.exit(0) end
  if code == false then return false, "code trop long (max " .. MAX_CODE .. " octets)" end

  local env = player_env()
  local chunk, err = _load(code, "=ton_code", "t", env)
  if not chunk then return false, err end

  budget = MAX_INSTR
  sethook(hook, "", HOOK_STEP)
  local ok, res = _pcall(function()
    chunk()
    local x = rawget(env, "x")
    local check = _assert(_load(lvl.check, "=check", "t", check_env(x)))
    check()
  end)
  sethook()
  if not ok then return false, errmsg(res) end
  return true
end

write([[
     _                      _       _        _
    / \   ___ ___  ___ _ __| |_    | |_ ___ (_)
   / _ \ / __/ __|/ _ \ '__| __|___| __/ _ \| |
  / ___ \\__ \__ \  __/ |  | ||_____| || (_) | |
 /_/   \_\___/___/\___|_|   \__|     \__\___/|_|

Lua 5.4. Pour chaque niveau, envoie du code qui définit la globale `x`
pour que les vérifications passent. Termine ton code par une ligne `EOF`.

Disponibles : assert error pcall xpcall type tostring tonumber select
next pairs ipairs rawget rawset rawequal rawlen getmetatable setmetatable
string table math utf8 print

]])

for i, lvl in ipairs(LEVELS) do
  write(("=== Niveau %d/%d : %s ===\n%s\n\n"):format(i, #LEVELS, lvl.name, lvl.check))
  while true do
    write("> ")
    local ok, err = run_level(lvl)
    if ok then
      write("Bien joué !\n\n")
      break
    end
    write("Raté : ", err, "\n")
  end
end

write("Tu maîtrises les metatables. Voilà ton dû : ", FLAG, "\n")
