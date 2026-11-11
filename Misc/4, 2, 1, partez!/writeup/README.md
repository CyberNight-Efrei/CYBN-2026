# 4, 2, 1, partez! - Writeup

Le fichier `chall.wav` est une suite de notes séparées par de courts silences.

En l'ouvrant dans Audacity, on remarque que les notes n'ont que deux durées possibles :
> - courtes (~80ms)
> - longues (~160ms).

Le titre évoque la conjecture de Syracuse (Collatz) : 
> toute suite `n -> n/2` (si `n` est pair) ou `n ->  3n+1` (si `n` est impair) 
> finit par tomber dans le cycle `4, 2, 1`. 

Le fichier se termine *courte, courte, longue*, soit `4` (pair), `2` (pair), `1` (impair).
-> comprendre donc: courte: pair (`0`), longue: impair (`1`).

La suite des parités suffit à retrouver le nombre de départ. 
On part de `1` et on remonte la suite en lisant les bits à l'envers :

- bit `0` : le terme précédent était pair, il valait `2n` ;
- bit `1` : le terme précédent était impair, il valait `(n - 1) / 3`.

Le nombre obtenu, converti en octets (big-endian), donne le flag.

Le solveur organisateur reproduit directement ces étapes :

```bash
python writeup/solve.py dist/chall.wav
```

Il affiche (la chaîne de bits est omise) :

```text
1246 notes
...
1651384534487246524851609095580915114099103928753284738429
b'CYBN{Wh4t_4n_0dd_rhy7hm}'
```

Flag : `CYBN{Wh4t_4n_0dd_rhy7hm}`
