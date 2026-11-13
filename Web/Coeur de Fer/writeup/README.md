# Writeup : Coeur de Fer

Challenge **Web + Crypto**. Deux étapes :
1. **Web** : forger un profil dont le hash faible (signature de cœur) égale celui de l'âme sœur.
2. **Crypto** : déchiffrer en XOR le numéro de l'âme sœur avec sa date de naissance.

Flag par défaut : `CYBN{r0b0t_l0v3_x0r3d_h34rt}`

---

## 1. Reconnaissance
- Sur la page, la carte **« ??? / PROFIL CRYPTÉ »** est l'âme sœur. Elle affiche
  sa **signature de cœur cible** (ex. `EFB9`) mais cache son profil.
- Le code JS contient la fonction de hash, visible côté client :
```js
function heartSig(s){
  let h=0x1234;
  for(let i=0;i<s.length;i++){ h=((h<<5) ^ (h>>2) ^ s.charCodeAt(i)) & 0xFFFF; }
  return h;
}
```
C'est un hash **16 bits** (seulement 65 536 valeurs) : trivial à inverser par force brute.

## 2. Forger le profil (web)
Il faut un nom (ou `nom|traits`) dont `heartSig` vaut la signature cible.
La signature cible se lit dans la carte verrouillée, ou via `GET /candidates`
(champ `sig` de l'entrée `locked: true`).

Brute force d'un préimage :
```python
def heart_sig(s):
    h=0x1234
    for ch in s: h=((h<<5)^(h>>2)^ord(ch))&0xFFFF
    return h

target=0xEFB9
i=0
while heart_sig("bot%d"%i)!=target: i+=1
print("bot%d"%i)   # ex: bot4581
```

## 3. Déclencher le match
Envoyer le profil forgé :
```bash
curl -s -X POST http://localhost:8011/match --data-urlencode "name=bot4581" -d "traits="
```
Réponse (match) :
```json
{
  "matched": true,
  "soulmate": {
    "name": "Vénus-9",
    "birthdate": "2041-07-14",
    "enc_numero": "7169767f5642074f01406d5c04471e6f4f1d4307566f5c0219424350"
  }
}
```

## 4. Déchiffrer (crypto)
Le numéro est chiffré en XOR répété avec la date de naissance `2041-07-14` :
```python
enc=bytes.fromhex("7169767f5642074f01406d5c04471e6f4f1d4307566f5c0219424350")
key=b"2041-07-14"
print(bytes(enc[i]^key[i%len(key)] for i in range(len(enc))).decode())
# CYBN{r0b0t_l0v3_x0r3d_h34rt}
```
Équivalent CyberChef : `From Hex` -> `XOR` clé `2041-07-14` (UTF8).

## 🏁 Flag
```
CYBN{r0b0t_l0v3_x0r3d_h34rt}
```

## Notes pédagogiques
- La vuln web : **hash faible, préimage triviale** (espace 16 bits) + vérification côté serveur qu'on satisfait avec un simple brute force.
- La vuln crypto : **XOR à clé connue et courte** (la date de naissance est livrée avec le ciphertext).
- Le serveur recalcule bien le hash : on ne peut pas juste « mettre » la bonne signature, il faut un vrai préimage.
- Changer le flag : variable `FLAG` (définie dans le `Dockerfile`). Le `enc_numero`
  est recalculé au démarrage, donc le ciphertext ci-dessus ne vaut que pour le flag par défaut.

## Script de résolution

`solve.py` enchaîne les deux étapes (préimage + match + déchiffrement XOR) :
```bash
pip install requests
python solve.py http://localhost:8011
```
