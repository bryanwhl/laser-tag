#include <CRCx.h>
#define BEETLE_ID '2' // change based on beetle
#define ACK_ID '0'
#define HANDSHAKE_ID '1'
#define WAKEUP_ID '2'
#define VEST_ID '4'

#include <IRremote.h>
const int RECV_PIN = 3;
IRrecv irrecv(RECV_PIN);
decode_results results;
char hpLevel = 'X';

//constants
char HANDSHAKE[]  = "HANDSHAKE";
char ACK[]        = "ACK";
char WAKEUP[]     = "WAKEUP";
char ZEROVEST[]   = "0VEST";
char ONEVEST[]    = "1VEST";
int PACKET_SIZE   = 20;


//create variable to be used for packet and data processing
uint8_t data[16];
uint8_t packet[20];
float data_set[6];
int seq_num = 0;
int hp = 100;

//boolean checks for logic program
//check that data transfer has begin
//check if receive error or handshake from laptop
bool error          = false;
bool handshake      = false;
bool handshake_ack  = false;
bool data_ack       = false;
bool data_sent      = false;
unsigned long TIMEOUT = 1000;
unsigned long sent_time;
volatile int activation_count = 0;

void setup() {
  Serial.begin(115200);

  irrecv.enableIRIn();
  irrecv.blink13(true);
  pinMode(14, OUTPUT);
  pinMode(15, OUTPUT);
  pinMode(17, OUTPUT);
  hp = 100;

  sent_time = millis();
  error = false;
  handshake = false;
  handshake_ack = false;
  data_ack = false;
  data_sent = false;
  seq_num = 0;
  delay(100);
}

//Add # to pad string to 16 char.
void data_padding(char msg[]) {
  int len = strlen(msg);
  int j = 0;
  for (int i = 0; i < 16; i = i + 1) {
    if (16 - i >  len ) {
      data[i] = '#';
    } else {
      data[i] = msg[j];
      j = j + 1;
    }
  }
}

//Attach packet_id, packet_no and crc to data
void packet_overhead(char packet_id) {
  uint8_t result8 = crcx::crc8(data, 16);
  String temp = String(result8, HEX);
  char crc[3];
  temp.toCharArray(crc, 3);
  int j = 0;

  //heading for packet
  packet[0] = BEETLE_ID;
  packet[1] = packet_id;

  // insert data into body of packet
  for (int i = 2; i < 18; i = i + 1) {
    packet[i] = data[j];
    j = j + 1;
  }

  // add crc to last 2 bit of packet
  if (strlen(crc) == 1) {
    packet[18] = '0';
    packet[19] = crc[0];
  } else {
    packet[18] = crc[0];
    packet[19] = crc[1];
  }//*/
}

void loop() {
  //if dont recieve ACK from laptop, send the next set. Not applicable for motion sensor
  if (millis() - sent_time >= TIMEOUT) {
    error = true;
  }

  if (Serial.available()) {
    byte cmd = Serial.read();
    switch (cmd) {
      case '0':
        if (seq_num == 0) {
          data_ack = true;
          data_sent = false;
          error = false;
          activation_count -= 1;
          seq_num = 1;
        }
        break;
      case '1':
        if (seq_num == 1) {
          data_ack = true;
          data_sent = false;
          error = false;
          activation_count -= 1;
          seq_num = 0;
        }
        break;
      case 'A': //Received ACK
        data_ack = true;
        if (handshake) {
          handshake_ack = true;
          handshake = false;
          delay(100);
        }
        break;
      case 'H'://Received Handshake request
        data_padding(HANDSHAKE);
        packet_overhead(HANDSHAKE_ID);
        Serial.write((char*)packet, PACKET_SIZE);
        memset(data, 0, 16);
        sent_time = millis();
        handshake = true;

        //Reset all boolean to default since handshake req is only when connecting/reconnecting
        error = false;
        handshake_ack = false;
        data_ack = false;
        data_sent = false;
        seq_num = 0;
        break;
      case 'W' ://Received Wakeup Call
        data_padding(WAKEUP);
        packet_overhead(WAKEUP_ID);
        Serial.write((char*)packet, PACKET_SIZE);
        memset(data, 0, 16);
        break;
      default:
        data_padding(ACK);
        packet_overhead(ACK_ID);
        Serial.write((char*)packet, PACKET_SIZE);
        memset(data, 0, 16);
        hp = (int)((char)cmd - 'a') * 10;
        break;
    }
  }

  delay(30);
  if (handshake && !handshake_ack && error) {
    data_padding(HANDSHAKE);
    packet_overhead(HANDSHAKE_ID);
    Serial.write((char*)packet, PACKET_SIZE);
    sent_time = millis();
    error = false;
  }

  //stop and wait for gun and vest
  if (data_ack && !data_sent && handshake_ack && activation_count > 0) {

    if (seq_num == 0) {
      data_padding(ZEROVEST);
    } else if (seq_num == 1) {
      data_padding(ONEVEST);
    }
    packet_overhead(VEST_ID);
    Serial.write((char*)packet, PACKET_SIZE);

    data_sent = true;
    data_ack = false;
    sent_time = millis();
    error = false;
  }

  if (error && data_sent) {

    if (seq_num == 0) {
      data_padding(ZEROVEST);
    } else if (seq_num == 1) {
      data_padding(ONEVEST);
    }
    packet_overhead(VEST_ID);
    Serial.write((char*)packet, PACKET_SIZE);

    data_ack = false;
    sent_time = millis();
    error = false;
  }

  if (irrecv.decode()) {
    activation_count += 1;
    delay(300);
    irrecv.resume();
    hp -= 10;
  }

  if (hp >= 70) {
    hpLevel = 'h';
  } else if (hp >= 40) {
    hpLevel = 'm';
  } else if (hp >= 0) {
    hpLevel = 'l';
  } else {
    hpLevel = 'x';
  }

  switch (hpLevel) {
    case 'l': // hp >= 0
      digitalWrite(14, LOW);
      digitalWrite(15, LOW);
      digitalWrite(17, HIGH);
      break;
    case 'm': // hp >= 40
      digitalWrite(14, LOW);
      digitalWrite(15, HIGH);
      digitalWrite(17, HIGH);
      break;
    case 'h': // hp >= 70
      digitalWrite(14, HIGH);
      digitalWrite(15, HIGH);
      digitalWrite(17, HIGH);
      break;
    case 'x': //
      digitalWrite(14, LOW);
      digitalWrite(15, HIGH);
      digitalWrite(17, LOW);
      break;
    default:
      digitalWrite(14, HIGH);
      digitalWrite(15, LOW);
      digitalWrite(17, HIGH);
      break;
  }
}
