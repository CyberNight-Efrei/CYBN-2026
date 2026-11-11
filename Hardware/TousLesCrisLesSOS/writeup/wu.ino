void setup() {
  Serial.begin(115200);
  pinMode(6, INPUT);
}

void loop() {
  Serial.print(digitalRead(6));
}

// On lance le programme, puis plus qu'à décoder le morse
