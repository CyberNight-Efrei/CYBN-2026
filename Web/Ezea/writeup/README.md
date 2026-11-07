# ezea — profil introuvable

**Catégorie :** Web · **Difficulté :** Medium

## Résumé

`ezea` est un annuaire d'étudiants. Un étudiant a fait opposition à la
publication de son profil (`visibility = PRIVATE`) : il n'apparaît plus dans
l'annuaire. Mais le filtrage de visibilité n'est appliqué qu'à **un seul**
resolver de l'API GraphQL. Toute autre voie qui renvoie un objet `Student`
laisse fuiter le profil masqué — et l'URL de son CV, dont le PDF contient le
flag.

## Faille

Le front (`/static/script.js`) interroge `/graphql`. L'endpoint a
l'introspection activée.

Le schéma contient :

- `Query.students` — **filtre** `visibility = PUBLIC` (listing public).
- `Query.student(id)` — **ne filtre pas** (accès unitaire par id).
- `Tag.students` — **ne filtre pas** (projection des étudiants d'un tag).

Le filtre de visibilité vit dans le resolver `students`, pas dans le type
`Student` ni dans les autres resolvers qui renvoient des `Student`. C'est le
bug classique du contrôle d'accès posé au mauvais niveau.

Le champ `cvUrl` expose `/cv/<token>.pdf`, où `token` est aléatoire (donc non
devinable), mais il est renvoyé par GraphQL dès qu'on obtient l'objet
`Student`.

## Exploitation

1. Repérer l'endpoint `/graphql` dans l'onglet réseau (le front s'en sert pour
   peupler l'annuaire). L'introspection est ouverte, on lit le schéma.

2. Lister les tags et leurs étudiants — ce chemin ne filtre pas :

   ```graphql
   { tags { name students { id name visibility cvUrl } } }
   ```

   Le profil `PRIVATE` apparaît (tag `defense` / `clearance`), avec son `cvUrl`.

   Variante équivalente si on devine/récupère l'id : `student(id: "...")`.

3. Télécharger le PDF pointé par `cvUrl` → le flag est dans le CV.

Script complet : [`solve.py`](solve.py).

```
python solve.py http://127.0.0.1:5000
```

## Flag

```
CYBN{l34ky_gr4phql_r3s0lv3r}
```
