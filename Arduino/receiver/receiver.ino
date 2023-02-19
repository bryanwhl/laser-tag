#include <IRremote.h>

const int RECV_PIN = 3;
IRrecv irrecv(RECV_PIN);
decode_results results;
int hp;

void setup(){
  Serial.begin(9600);
  irrecv.enableIRIn();
  irrecv.blink13(true);
  pinMode(14, OUTPUT);
  pinMode(15, OUTPUT);
  pinMode(17, OUTPUT);
  hp=100;
}

void loop(){
  if (irrecv.decode()){
        Serial.println(irrecv.decodedIRData.address);
        Serial.println(irrecv.decodedIRData.command);
        hp -=10;
        delay(500);
        if (hp <= 0){
          hp = 100;
        }
        irrecv.resume();
  }
  if (hp >= 70) {
    digitalWrite(14, HIGH);
    digitalWrite(15, HIGH);
    digitalWrite(17, HIGH);
  }
  else if (hp >= 40) {
    digitalWrite(14, LOW);
    digitalWrite(15, HIGH);
    digitalWrite(17, HIGH);
  }
  else if (hp > 0) {
    digitalWrite(14, LOW);
    digitalWrite(15, LOW);
    digitalWrite(17, HIGH);
  }
}
