# Snoop Log — Writeup

## Énoncé

> En analysant le téléphone d'un admin, on est tombé sur un log Bluetooth. On est sûrs que quelque chose d'important est caché dedans.

Fichier fourni : `BT_HCI_2026_1117_181033.cfa`

Le fichier est un **HCI snoop log** Android (format btsnoop). Il contient un flux audio **A2DP** envoyé par le téléphone à des écouteurs Bluetooth. Il suffit d'extraire les trames **SBC** des paquets **RTP**, de les décoder en `.wav` et d'écouter : une voix épelle le flag.

L'extension `.cfa` n'est pas parlante, mais la commande `file` l'est :

```
$ file BT_HCI_2026_1117_181033.cfa
BT_HCI_2026_1117_181033.cfa: BTSnoop version 1, HCI UART (H4)
```

**btsnoop** est le format du *Bluetooth HCI snoop log*. C'est une option développeur d'Android qui enregistre tout ce qui passe entre le système du téléphone et sa puce Bluetooth.

Ce journal est pris **à l'intérieur du téléphone**. La liaison radio avec les écouteurs est chiffrée, mais la puce Bluetooth déchiffre les données avant de les remonter au système : dans le log, tout est en clair.

Wireshark ouvre ce format directement.

On ouvre le fichier, puis **Statistics → Protocol Hierarchy** :

```
bluetooth
  hci_h4
    bthci_cmd / bthci_evt      commandes et événements de la puce
    bthci_acl
      btl2cap
        btsdp                  découverte de services
        btrfcomm → bthfp       profil kit mains-libres (commandes AT)
        btavdtp                signalisation audio
        btavctp → btavrcp      télécommande (lecture / pause)
        bta2dp → rtp → sbc     1509 trames, ~97 % des données
```

Les appareils sont identifiés dès les premières trames : un **Redmi Note 12S** (le téléphone) et des écouteurs **JBL TUNE BEAM**.

La branche intéressante saute aux yeux : **A2DP** (*Advanced Audio Distribution Profile*), le profil Bluetooth qui diffuse de l'audio stéréo vers un casque. Presque tout le volume du fichier est là : le téléphone a envoyé du son aux écouteurs pendant la capture.


Avant d'envoyer le son, téléphone et écouteurs se mettent d'accord sur le codec avec **AVDTP**. Filtre `btavdtp`, puis on regarde le message **SetConfiguration** :

```
Media Codec - Audio SBC (44100 | JointStereo | block: 16 | subbands: 8 | allocation: Loudness | bitpool: 2..53)
```

Le codec est **SBC** (*Low Complexity Subband Coding*), le codec obligatoire de l'A2DP, en 44,1 kHz stéréo. 

ffmpeg sait le décoder nativement.

On voit ensuite les commandes `Open`, `Start`, puis le flux, puis `Suspend` et `Close` à la fin de la lecture.

Pour reconstituer l'audio, on retire les en-têtes RTP et SBC de chaque paquet, puis on met les trames SBC bout à bout, dans l'ordre.

Par défaut, Wireshark décode les trames SBC. On désactive ce décodeur (`--disable-protocol sbc`) : la charge utile RTP apparaît alors dans le champ `data`. On retire le premier octet (l'en-tête média SBC, soit 2 caractères hexa), puis on reconvertit en binaire :

```bash
tshark -r BT_HCI_2026_1117_181033.cfa --disable-protocol sbc -Y bta2dp -T fields -e data \
  | cut -c3- | xxd -r -p > flag.sbc
```

```bash
ffmpeg -f sbc -i flag.sbc flag.wav
```

On obtient environ 22 secondes d'audio.

À l'écoute, une voix dicte un mot de passe caractère par caractère :

> C, Y, B, N, accolade ouvrante, 3, 4, R, B, U, D, S, underscore, T, 0, L, D, underscore, M, 3, accolade fde fin.

## Flag

```
CYBN{34RBUDS_T0LD_M3}
```
