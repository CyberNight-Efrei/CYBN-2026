# Pourquoi être aussi corrompu

Le DOCX est une archive ZIP dont le fichier `word/document.xml` a été tronqué. Word ne l'ouvre plus, mais l'image du schéma est intacte. On peut l'extraire directement :

```sh
unzip -p ../public/documentation.docx word/media/image1.png > schema.png
```

Avec 7-Zip :

```powershell
7z x ../public/documentation.docx -oextraction
```

Le schéma nomme la machine de secours `PH3N1X-02`. Le flag est `CYBN{PH3N1X-02}`.
