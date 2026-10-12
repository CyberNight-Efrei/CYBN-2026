# Citadelle never dies - Getting started

Le score est envoyé à `POST /api/scores` avec une signature HMAC-SHA256 du payload, calculée côté client.

La clé est dans le bundle JS, découpée en trois morceaux obfusqués (un caractère sur deux, des charCodes décalés, une chaîne inversée). On peut la reconstruire à la main, ou simplement poser un breakpoint sur `crypto.subtle.importKey` : `Citadelle-N3v3r-D13s-howdy-7Fq2Zk`.

Il ne reste plus qu'à signer un payload avec 1e12 écus : [solve.js](solve.js)

`CYBN{H4cK1nG_Th3_Tr34sUry_1s_3z}`
