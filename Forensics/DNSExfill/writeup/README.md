# Je demande pour un ami

Dans Wireshark, filtrer les requêtes avec `dns.qry.name contains "evil.cybn.fr"`. Les noms suspects suivent le format `0000.bloc.evil.cybn.fr`. Le premier label donne l'ordre des blocs ; le second contient un morceau de la note en Base64 URL-safe, sans padding. Les autres requêtes DNS et les échanges HTTP servent de trafic ordinaire.

Pour reconstruire la note depuis le seul PCAP :

```sh
python -m pip install -r requirements.txt
python solve.py
```

Le script trie les blocs, rétablit le padding Base64 et affiche le texte UTF-8. La référence à la fin de la note est le flag : `CYBN{N11LYX_CL1GN3_D35_Y3UX_M415_V01T_T0UT}`.
