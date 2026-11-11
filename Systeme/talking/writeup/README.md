Bon alors celui-là on se marre

Dans l'infra de la CYBN, une machine broadcast des messages en continu

Le titre et la description tendent à indiquer un broadcast : un message envoyé sur l'IP qui finit en .255, pour un réseau classique

En recherchant cela dans graylog, on voit cela :
``
10.64.0.101 -> 10.64.1.255:2121
``

On sait alors quelle machine dialogue... mais pour le moment impossible de lire le contenu des paquets.

L'adresse réseau des joueurs (VPN comme WiFi) n'est **PAS** 10.64.1.0/24, elle est différente.

Pour pouvoir lire les paquets, il faut alors le faire depuis une machine du réseau.

Comment faire....

...

Vous voyez où je veux en venir ?

=> On va utiliser une machine d'un autre challenge :D

Au moins 4 challenges de la catégorie "System" permettent de se connecter en SSH à une machine de l'infra.

Note : oui il s'agit de conteneurs, donc cela devrait être un réseau privé spécifique. On fait abstraction de cela ici, l'infra a été pensée pour rendre le tout crédible, on va bien voir les paquets. Trust the system.

On réussit alors un challenge, par exemple "Alicia au pays des miracles", on devient root (nécessaire pour capture le réseau), et on peut alors lancer une commande de capture de paquets :
``
tcpdump port 2121
``

On voit bien le trafic.
On peut désormais exporter le résultat dans un fichier, que l'on va extraire du serveur via la commande ``scp``

```
tcpdump port 2121 -w /tmp/talking.pcap

scp user@challenge:/tmp/talking.pcap . -P 10123
```

Une fois ouvert avec wireshark, 2 types de paquets UDP sont identifiables, avec les infos suivantes :
```
USER=JohnNeuill
PASS=Cyb3rNightist@n
```

Le port ciblé est 2121, et les identifiant donnés laissent tout deux penser à une chose : un serveur **FTP**

On se connecte alors au port 2121 de la machine qui émet les messages (10.64.0.101) en FTP, avec les identifiants fournis

Et comme par magie, un fichier ``flag.txt`` apparait :
> ``CYBN{L0ngU3_v13_Au_P4y5_dU_CYb3rN1Gh71St@n}``