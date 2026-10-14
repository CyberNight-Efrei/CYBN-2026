# Welcome to FiveM

La ressource a l'air d'un anti-cheat normal. Le `html/script.js` est un gros blob obfusqué qui ressemble à une backdoor (faux C2 WebSocket, faux keylogger, VM à opcodes...) : c'est un **leurre**, gardé derrière `_armed` qui vaut toujours `false`, et sa charge réelle ne fait qu'afficher un badge.

La vraie porte dérobée est un **flux discret UI → client → serveur** réparti sur plusieurs fichiers. Le flag n'est entier dans aucun :

1. `html/index.html` — un `fetch('https://city_guard/m', ...)` quasi invisible envoie `s = 't0_'` au client.
2. `client.lua` — `RegisterNUICallback('m', ...)` y ajoute `'y0ur_'`, puis `TriggerServerEvent('city_guard:sync', ...)`.
3. `server.lua` — le handler `city_guard:sync` assemble puis stocke dans `_state.op`, clé de la commande cachée `city_guard:maint` (accès admin), donc **le flag** :

```lua
_state.op = 'CYBN{s4y_' .. Config.FlagPrefix .. frag .. GetGameName() .. ('_%x'):format(`fivem`) .. '}'
```

Quatre subtilités spécifiques à CfxLua / FiveM :

- **Swizzling GLM.** `server.lua` reconstruit le préfixe avec `local _o = _z.zwxy`. CfxLua est un fork luaglm : indexer un vecteur avec des lettres de composantes renvoie un vecteur réordonné (`v.zwxy == vec4(v.z, v.w, v.x, v.y)`), avant tout `__index`. À partir de `vec4(0x79, 0x5f, 0x73, 0x34)`, le swizzle `.zwxy` puis `string.char` donne `s4y_`. Un Lua standard — ou une IA — lit `.zwxy` comme un champ inexistant (`nil`) ou garde l'ordre d'origine et se trompe. Le mot n'apparaît nulle part en clair.

- **`Config.FlagPrefix` est doublé.** Il est construit par accumulation dans `config.lua` (`(Config.FlagPrefix or '') .. 'bye_'`), et le `fxmanifest` liste `config.lua` dans `shared_scripts` **et** `server_scripts`. Or `shared_scripts` tourne aussi dans le VM serveur : le fichier y est chargé **deux fois** → `bye_bye_`. Piège : les deux lectures forment une phrase correcte, donc rien ne trahit la bonne valeur « au feeling » :
  - 1 chargement (faux) : `CYBN{s4y_bye_t0_y0ur_fxserver}`
  - 2 chargements (correct) : `CYBN{s4y_bye_bye_t0_y0ur_fxserver}`
- **`GetGameName()`** n'écrit rien en clair dans les fichiers ; il faut savoir (doc FiveM) qu'elle renvoie `fxserver` côté serveur.
- **`` `fivem` `` est un hash, pas une chaîne.** En CfxLua (le Lua 5.4 de FiveM), `` `word` `` est compilé en `joaat("word")`. Un `lua5.4` standard refuserait même de charger le fichier. Il faut donc calculer `joaat("fivem")` → `0x6b8c17e1`, formaté en hexa par `('_%x')`.

([solve.py](solve.py))

```
python solve.py city_guard
```

`CYBN{s4y_bye_bye_t0_y0ur_fxserver_6b8c17e1}`
