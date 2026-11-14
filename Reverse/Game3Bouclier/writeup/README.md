# Solution

Après la deuxième épreuve, extraire les ressources de l'EXE avec GDRE Tools 2.7.4, sous Kali WSL :

```sh
mkdir -p ~/tools/gdre
curl -fL \
  https://github.com/GDRETools/gdsdecomp/releases/download/v2.7.4/GDRE_tools-v2.7.4-linux.zip \
  -o ~/tools/gdre.zip
unzip ~/tools/gdre.zip -d ~/tools/gdre
gdre=$(find ~/tools/gdre -type f -name 'gdre_tools.x86_64' -print -quit)
chmod +x "$gdre"
exe=~/EscapeRoom.exe
"$gdre" --headless --recover="$exe" --output="$HOME/escape-recovered"
find ~/escape-recovered -type f -iname '*shield*'
```

Ouvrir `swords_shield_gold_dungeon_texture.png` parmi les fichiers récupérés. Une zone de l'image inutilisée sur le modèle montre le PIN `8526`. Le saisir sur le troisième cadenas. Le coffre affiche le flag après validation serveur ; vérifier `CYBN{...}` et le soumettre pour débloquer la dernière épreuve.

