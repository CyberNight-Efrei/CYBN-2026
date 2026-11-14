# Solution

Extraire `EscapeRoom.exe` de l'archive fournie, puis le lancer pour créer une session. Sous Windows, lire la sauvegarde Godot :

```powershell
Get-Content "$env:APPDATA\Godot\app_userdata\EscapeRoom\savegame.json"
```

Relever la valeur de `pin_1`, l'entrer sur le premier cadenas et valider. Le serveur renvoie le flag, qui apparaît dans le coffre ouvert. Vérifier son format `CYBN{...}` et le soumettre sur la plateforme pour débloquer l'épreuve suivante. Le PIN change avec la session ; modifier la sauvegarde ou l'état visuel du jeu ne change pas le PIN attendu par le serveur.

