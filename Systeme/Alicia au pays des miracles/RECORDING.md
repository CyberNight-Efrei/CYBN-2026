# Enregistrement des sessions SSH

Notes de conception pour `cybn-record.sh` et la boucle `cybn_shipper` de
`entrypoint.sh`.

**Ce fichier ne doit jamais être copié dans l'image.** Le `Dockerfile` ne copie
que `cybn-record.sh`. Tout ce qui entre dans l'image est lisible par le joueur.

## Pourquoi la documentation est ici et pas dans le script

`cybn-record.sh` est en mode `555`. Un script shell doit être **lisible** pour
être exécuté : le joueur peut donc le lire. Une première version y expliquait
que le trafic tunnelisé échappait à l'enregistrement — ce qui désignait le
port forwarding comme pertinent, et donnait un indice sur la solution. Les
commentaires du script se limitent désormais à dire qu'il relève de
l'exploitation et non du challenge.

Les deux autres pièces ne sont pas exposées :

| Élément | Mode | Lisible par le joueur |
|---|---|---|
| `cybn-record.sh` → `/usr/local/bin/cybn-record` | `555` | **oui** |
| `entrypoint.sh` | `500`, root | non |
| `/var/log/cybn` | `1733` | non (ni liste ni lecture) |

## Ce qui est enregistré

`sshd` exécute `cybn-record` via `ForceCommand` à chaque session. Le script
enveloppe le shell dans `script(1)` et écrit deux fichiers dans `/var/log/cybn` :
`.out` (ce qui s'est affiché) et `.timing` (la cadence). La paire se rejoue avec
`scriptreplay`, comme un enregistrement asciinema.

## Ce qui n'est pas enregistré

Le trafic tunnelisé. Un canal `direct-tcpip` n'atteint jamais un shell : les
octets qui passent par un transfert de port sont invisibles pour un enregistreur
de terminal. Angle mort connu et accepté.

`LogLevel VERBOSE` avait été ajouté dans l'idée de journaliser l'ouverture des
canaux. **Cela ne fonctionne pas** : vérifié sur l'image, aucune ligne
`direct-tcpip` n'apparaît, ce message étant de niveau debug dans OpenSSH. Le
réglage est conservé pour le reste (authentifications, empreintes), mais il
n'apporte rien sur les tunnels. Pour les couvrir il faudrait `LogLevel DEBUG`
(bruyant, et déconseillé en production par OpenSSH), ou une capture sur la
boucle locale — `tcpdump` est déjà présent dans l'image, et le trafic tunnelisé
y circule en clair.

## Deux pièges rencontrés, à ne pas réintroduire

**Le script ne doit jamais empêcher une connexion.** Une version déréférençait
`$SSH_ORIGINAL_COMMAND` sans valeur par défaut sous `set -u` : dash sortait
avant `exec`, sshd fermait la session, et le joueur n'obtenait aucun shell. Une
transcription manquante est un trou dans les preuves ; un enregistreur qui
échoue est un challenge insoluble. D'où `fallback()`, appelée depuis chaque
branche, et une valeur par défaut sur chaque variable fournie par sshd.

**`tail -F | base64` n'expédie rien.** `base64` lit son entrée par blocs et ne
produit rien tant que son tampon n'est pas plein ou que l'entrée n'est pas
terminée — ce que `tail -F` ne fait jamais. La transcription ne partait donc
jamais. Un test manuel passait uniquement parce que `timeout` tuait `tail` et
forçait la fin de fichier. D'où la lecture par offset de `cybn_ship_new_bytes`,
où `base64` se termine à chaque tour.

## Format de sortie

Chaque ligne émise sur la sortie standard du conteneur :

```
CYBN-CAST <fichier> <offset> <longueur> <base64>
```

`offset` et `longueur` portent sur les octets bruts, ce qui permet de
réassembler dans l'ordre et de détecter un trou. Les morceaux sont bornés à
4000 octets : au-delà de 16 Ko, Docker scinde une ligne de log et casserait le
réassemblage.

Réassemblage puis relecture :

```sh
scriptreplay --timing=<clé>.timing --typescript=<clé>.out
```
