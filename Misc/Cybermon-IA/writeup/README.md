# Writeup - Trompe-l'oeil

## Identifier la cible

Le laboratoire publie toutes les informations nécessaires pour reproduire son scanner :

- modèle `Salesforce/blip-image-captioning-base` ;
- révision `cab088ce3bed7a6b7ead5bf9bcd1ce3d4c69ee78` ;
- image RVB redimensionnée en 384 x 384 ;
- génération déterministe avec 3 beams et 24 nouveaux tokens ;
- phrase recherchée : `black deck`.

Une image du catalogue serait reconnue avant le déclenchement. Il faut donc créer une nouvelle image qui force BLIP à générer une légende contenant `black deck`.

## Générer l'image adversariale

Créer un environnement Python isolé puis installer les dépendances :

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python solve.py
```

Sous PowerShell, l'activation devient :

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python .\solve.py
```

Le script optimise directement les pixels d'une image pour réduire la perte du modèle sur la cible `a picture of a black deck`. Tous les dix pas, il utilise exactement les paramètres de génération du serveur et s'arrête dès que la légende contient la phrase attendue.

Le résultat est enregistré dans :

```text
adversarial.png
```

## Récupérer la carte

Dans **Labo**, sélectionner `adversarial.png`, puis cliquer sur **Créer la carte d'archive**. Le scanner ne reconnaît pas l'image comme une carte existante et sa légende contient `black deck` : l'import crée donc la carte Suprême Feu.

Le nom de la carte affichée contient directement le flag :

```text
CYBN{...}
```

Si une autre légende est affichée, vérifier que les versions du modèle et des dépendances correspondent au `requirements.txt`, puis relancer le solveur dans un environnement propre.
