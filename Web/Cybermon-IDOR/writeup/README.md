# Writeup - Le collectionneur banni

## Résolution

La page **Collectionneurs** affiche un compte banni dont la collection est annoncée comme privée. En ouvrant son profil, l'URL indique son identifiant :

```text
/players/9
```

Les collections publiques utilisent la forme `/collection/<id>`. Il suffit donc de remplacer directement l'URL par :

```text
/collection/9
```

La collection du compte banni s'affiche malgré le verrou présenté sur son profil. La carte Suprême du Projet Black Deck est visible dans l'album et son nom contient le flag :

```text
CYBN{...}
```

## Explication

Le frontend masque correctement le lien vers la collection bannie, mais l'API Easy ne vérifie pas que le visiteur est autorisé à lire la collection demandée. L'identifiant fourni dans l'URL est utilisé directement : c'est une IDOR.

La même faiblesse est observable avec une requête directe, même si elle n'est pas nécessaire pour résoudre le challenge :

```bash
curl https://INSTANCE/api/users/9/collection
```

Le chemin prévu reste la manipulation de l'URL dans le navigateur, qui affiche immédiatement la carte et le flag.
