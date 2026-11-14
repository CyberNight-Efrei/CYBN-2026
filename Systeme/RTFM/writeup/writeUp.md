# Writeup — RTFM

> Vous connaissez les man pages ? On va faire un petit test alors.
> J'ai créé une lib qui s'appelle `get_flag`, à vous de trouver comment l'utiliser.

---


## Étape 1

```
man get_flag
```

La page `get_flag(1)` explique que ce n'est pas une commande mais une
**bibliothèque**. Elle rappelle les sections du manuel, le fait que les pages
sont des fichiers `.gz` lisibles avec `zcat`, et que `man` n'affiche qu'un
*rendu*. En bas, la rubrique **VOIR AUSSI** pointe vers `get_flag(3)` et
`get_flag(7)`.

## Étape 2

```
man 3 get_flag
```

`get_flag(3)` est la doc de la fonction, avec un **exemple de code complet** à
recopier et la ligne de compilation :

```
gcc -o solve solve.c -lgetflag
```

Le mot de passe est remplacé par `CHANGEME`. Si on compile tel quel :

```
./solve
get_flag: Permission denied
```

Il manque donc le bon mot de passe.

## Étape 3

```
man 7 get_flag
```

`get_flag(7)` liste les options utiles de `man` (`-k`, `-K`, `-s`, `-w`…), la
navigation dans `less`, et surtout : les lignes commençant par `.\"` en roff
sont des **commentaires jamais affichés**. L'indice final : le mot de passe est
dans la doc du **fichier de configuration** (donc section 5) et commence par
`gf_`.

## Étape 4

Recherche classique (nom + description) : rien.

```
man -k gf_
gf_: nothing appropriate.
```

Recherche dans le **contenu intégral** des pages :

```
man -K gf_
```

Cela trouve `getflag.conf(5)`. Mais en l'affichant, le mot de passe n'apparaît
nulle part : il est dans un commentaire roff.

## Étape 5

```
man -w getflag.conf
/usr/local/share/man/man5/getflag.conf.5.gz

zcat /usr/local/share/man/man5/getflag.conf.5.gz
```

Dans la source, on lit le commentaire laissé par l'« admin » :

```
.\" Mot de passe de get_flag(3) : gf_r34d_th3_s0urc3_n0t_th3_r3nd3r
```

## Étape 6

On reprend l'exemple de `get_flag(3)`, on remplace `CHANGEME` par le mot de
passe trouvé, on compile et on lance :

```
gcc -o solve solve.c -lgetflag
./solve
Sup3r4dm1NL3mDPvo1La!
```

La fonction renvoie le **mot de passe du compte root**.

## Le flag

```
su -
# (mot de passe : Sup3r4dm1NL3mDPvo1La!)
cat /root/flag.txt
CYBN{m4n_p4g3s_4r3_y0ur_b3st_fr13nds}
```

