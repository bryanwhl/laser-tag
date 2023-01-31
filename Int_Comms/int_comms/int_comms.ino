struct packet {
  char type;
  char pad;
  int seq_id;
  int a;
  int b;
  int c;
  int d;
  int e;
  int f;
  int g;
  int CRC;
};

void setup() {
  Serial.begin(115200);
  packet handshaking;
  handshaking.type = 'A';
  while (true) {
    if (Serial.available() && Serial.read() == 'H') {
      Serial.print(handshaking);
      break;
    }
    delay(10);
  }
}

void loop() {
  // Below is stop and wait prototype
  Serial.print("Send data")
  while (true) {
    if (Serial.available()) {
      if (Serial.read() == 'A') {
        break;
      } else if (Serial.read() == 'N') {
        Serial.print("Retransmit");
      }
    }
    delay(100);
  }
}
