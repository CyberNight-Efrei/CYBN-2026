# Solution

Après avoir validé le premier challenge, prendre une pièce dans le coffre et l'offrir à la statue. Le compteur affiché passe à 1. Attacher Cheat Engine à `EscapeRoom.exe`, chercher cette valeur avec le type `4 Bytes`, offrir une autre pièce, puis filtrer sur 2. Répéter jusqu'à isoler la valeur qui suit exactement le compteur mural.

Écrire `1000000` à cette adresse et laisser le jeu tourner. Le client détecte le seuil et demande la validation au serveur. La statue révèle le flag ; vérifier `CYBN{...}` et le soumettre pour débloquer la suite. La modification de la sauvegarde locale ou d'un simple affichage ne valide pas cette étape.

