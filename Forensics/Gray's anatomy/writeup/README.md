Tous les logs ont été drops par le serveur : y'a plus rien lol

Mais en gros :

- Connexion RDP : on recherche port 3389 ou LogonType 10, et on voit une seule connexion sur le compte ``Gray`` depuis l'IP **192.168.52.1**
- En cherchant les processus lancés par le même compte par la suite, on voit un historique de commandes PowerShell, dont un téléchargelent du scropt : **``C:\Users\Public\Music\784dcff34b5a4c06b3dd8c729cf2243c\7639839a5e4a4511b93bb9ed654c2919.ps1``**
- Gràce au nom du malware, on peut désormais rechercher d'autres occurrences pour trouver une autre commande PowerShell créant une tâche plmanifiée. Cette dernière sert à exécuter le malware téléchargé avant. La tâche s'appelle **FirefoxUpdater**
- Dans la première exécution du malware, on voit alors l'IP contactée : **172.20.101.12**

Le flag est alors :
> CYBN{192.168.52.1_C:\Users\Public\Music\784dcff34b5a4c06b3dd8c729cf2243c\7639839a5e4a4511b93bb9ed654c2919.ps1_FirefoxUpdater_172.20.101.12}