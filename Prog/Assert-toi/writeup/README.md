# Assert-toi

*Tout est possible en Lua, il suffit de demander gentiment à la metatable.*

---

Le service présente 11 niveaux. Pour chacun, il affiche un bloc de vérifications et attend du code Lua (terminé par une ligne `EOF`) qui définit la globale `x`. Le code du joueur tourne dans un environnement restreint, et les vérifications dans un environnement séparé avec les vraies fonctions de base : redéfinir `assert` ou `type` ne sert donc à rien.

Le script complet est dans [`solve.py`](solve.py) : `python solve.py <host> <port>`.

## 1. Échauffement : `__add`

```lua
assert(x + 1 == 1337)
```
```lua
x = setmetatable({}, {__add = function() return 1337 end})
```

## 2. Tout le monde s'appelle CYBN : `__index`

`next(x) == nil` interdit de stocker quoi que ce soit dans la table. `__index` est appelé pour toute clé absente.
```lua
x = setmetatable({}, {__index = function() return "CYBN" end})
```

## 3. Le vide qui pèse lourd : `__len`

```lua
x = setmetatable({}, {__len = function() return 1337 end})
```

## 4. Compte jusqu'à trois : `__call` avec état

Une table appelable, et un compteur dans une upvalue.
```lua
local n = 0
x = setmetatable({}, {__call = function() n = n + 1 return n end})
```

## 5. Crise d'identité : NaN

Piège : `__eq` n'est **jamais** appelé quand on compare un objet à lui-même (`rawequal` court-circuite), donc aucune table ne peut vérifier `x ~= x`. Sauf qu'ici, rien n'impose une table…
```lua
x = 0/0
```

## 6. Ni plus, ni moins : `__lt` / `__le`

`a > b` est réécrit en `b < a`, donc `__lt` sert aux deux. En Lua 5.4, `__le` n'est plus déduit de `__lt` et doit être défini séparément. Les métaméthodes de comparaison marchent entre une table et un nombre.
```lua
x = setmetatable({}, {
  __lt = function() return true end,
  __le = function() return false end,
})
```

## 7. Un de plus, ça change rien : `__eq`

`__eq` n'est appelé que si les deux opérandes sont des tables (distinctes). `__add` doit donc renvoyer une **nouvelle** table portant la même metatable.
```lua
local mt = {}
mt.__eq = function() return true end
mt.__add = function() return setmetatable({}, mt) end
x = setmetatable({}, mt)
```

## 8. Chassé-croisé : `__newindex` + proxy

`__newindex` n'est déclenché que pour les clés absentes. Comme on ne stocke rien dans `x` lui-même, chaque écriture passe par lui. On redirige vers une table cachée en inversant `a` et `b`.
```lua
local store, swap = {}, {a = "b", b = "a"}
x = setmetatable({}, {
  __newindex = function(_, k, v) store[swap[k] or k] = v end,
  __index = store,
})
```

## 9. Déguisement : `__tostring`, `__concat`, `__metatable`

`__concat` est appelé que `x` soit à gauche ou à droite. Le champ `__metatable` est renvoyé par `getmetatable` et bloque `setmetatable`.
```lua
x = setmetatable({}, {
  __tostring = function() return "CYBN" end,
  __concat = function(a, b) return tostring(a) .. tostring(b) end,
  __metatable = "touche pas",
})
```

## 10. Boucle infinie (ou presque) : `__call` comme itérateur

`for v in x do` appelle `x` à chaque tour jusqu'à recevoir `nil`. Une table avec `__call` fait l'affaire.
```lua
local vals, i = {1000, 300, 37}, 0
x = setmetatable({}, {__call = function() i = i + 1 return vals[i] end})
```

## 11. Ferme la porte en sortant : `__close` (Lua 5.4)

Une variable `<close>` appelle `__close` à la sortie de son bloc.
```lua
x = setmetatable({}, {__close = function(self) self.closed = (self.closed or 0) + 1 end})
```

```
CYBN{m3t4t4bl3s_4r3_my_r34l_fr13nds_94951a4d}
```
