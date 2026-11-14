# Tous les cris les SOS

*(j'adore Daniel Balavoine)*

L'énoncé est clair : il faut envoyer la valeur du pin 2 en série au programme Python. Pour cela, rien de plus difficile : on initialise `Serial` à 115200 bauds pour avoir le taux d'échantillonnage le + élevé possible, on récupère le niveau logique du pin avec `digitalRead()` (oui, ça fonctionne pour lire les valeurs à 3.3V) puis on evoie tout avec `Serial.print` (sans le `ln` pour gagner en taux d'échantillonnage).

Plus qu'à décoder le morse à la main, les SOS du début indiquent les délais.

wu.ino
```cpp
void setup() {
  Serial.begin(115200);
  pinMode(6, INPUT);
}

void loop() {
  Serial.print(digitalRead(6));
}

// On lance le programme, puis plus qu'à décoder le morse
```

Ne pas oublier de modifier le port dans le programme Python !
