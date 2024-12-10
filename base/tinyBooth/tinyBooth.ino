
#define PIN_CB 4
#define PIN_RASPI 1
#define DELAY_RASPI 300

void setup() {
  pinMode(PIN_CB, INPUT);
  pinMode(PIN_RASPI, OUTPUT);
  digitalWrite(PIN_RASPI, LOW);
}

void loop() {
  // Postman
  if(digitalRead(PIN_CB)){
    digitalWrite(PIN_RASPI, HIGH);
    delay(DELAY_RASPI);
    digitalWrite(PIN_RASPI, LOW);
  }
}
