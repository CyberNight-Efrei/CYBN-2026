Write-up Builtins

En arrivant dans le chall pas le droit aux commandes plutôt classique comme ls.

`help` affiche toutes les commandes disponibles donc plein de manières de résoudre le chall.

Solution Basique:
`echo *`

On voit Trois dossiers (en vrai c'est deux mais c'est un bait)

on peut donc faire un `cd <uid>\ flag_dir`

Ensuite on reliste
`echo *`
et là rien, alors peut être fichier caché
`echo .*`
.passwd apparait, maintenant il faut le lire.

Suffit de lire la page de manuel de bash et dans Command Substitution on a la substitution de cat:
`echo $(<.passwd)`

# Bien joué, tu peux valider avec le flag suivant : CYBN{BASH_BUILTINS_POWER!!!}

Il existe de nombreux autres solutions comme par exemple:  
`history -r .passwd` pour ajouter le contenu du fichier dans l'historique
`enable -f head head` puis simplement `head .passwd` et oui certains builtins sont chargeables, ils sont situés dans /usr/lib/bash
