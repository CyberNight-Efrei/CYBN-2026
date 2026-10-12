# Citadelle never dies - Le trésorier

Au-delà de 1e15 écus, le serveur vérifie la cohérence de la partie et renvoie la raison de chaque refus. En les lisant une par une, on retrouve les règles :
- l'`eps` et le `clickPower` doivent correspondre aux upgrades
- `totalEcus` doit couvrir le prix des upgrades
- `totalEcus` ne doit pas dépasser ce que la partie a pu produire depuis `startedAt`

Or `startedAt` est envoyé par le client. On le recule jusqu'à la limite donnée par l'erreur (la fondation du royaume, le 23 mars 2026) : ça fait environ 6 mois de partie. Une seule Forge Éther suffit alors pour justifier 1e15 écus : [solve.js](solve.js)

`CYBN{Th3_Tr34sur3r_C4n_C0unt_bUt_N0t_W41t}`
