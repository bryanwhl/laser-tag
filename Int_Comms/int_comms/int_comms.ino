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

int id = 2;
int seq = 0;
packet vest;


void setup() {
  Serial.begin(115200);
  packet handshaking;
  handshaking.type = 'A';
  while (true) {
    if (Serial.available() && Serial.read() == 'H') {
      Serial.write(handshaking);
      break;
    }
    delay(10);
  }
}

void loop() {
  // Below is stop and wait prototype
  vest.type = 'V';
  seq_id = id * 10 + seq;
  Serial.write(vest);
  while (true) {
    if (Serial.available()) {
      if (Serial.read() == 'A') {
        break;
      } else if (Serial.read() == 'N') {
        Serial.print(vest);
      }
    }
    delay(100);
  }
}
