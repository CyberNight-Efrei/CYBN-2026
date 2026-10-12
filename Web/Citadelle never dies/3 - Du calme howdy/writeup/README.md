# Citadelle never dies - Du calme howdy

Au-delà de 1e18 écus, le serveur répond toujours `Du calme howdy 🤠`. La description donne quand même les deux règles :

- **il rejoue la partie achat par achat** : le client envoie `state.history`, une entrée `{ t, c, b }` par achat (ms depuis le début de session, clics depuis l'achat précédent, upgrade achetée). Chaque achat doit être payable avec les règles du bundle, à 15 clics/s maximum ;
- **il mesure le temps avec son sceau** : la durée de partie ne vient plus de `startedAt`, mais du `iat` du jeton `session` (`GET /api/session`, gardé dans le localStorage).

Atteindre 1e18 prend plusieurs centaines d'heures de jeu, même en jouant parfaitement. Mais le jeton est `base64url({sid, iat}).hmac`, et il est signé avec **la même clé** que les scores.

On simule donc une partie (achat glouton de la meilleure upgrade dès qu'elle est payable), puis on forge une session qui a commencé exactement quand la partie simulée aurait commencé : [solve.js](solve.js)

`CYBN{L4_C1t4d3ll3_N3_M3uRt_J4m41s_H0wdy}`
