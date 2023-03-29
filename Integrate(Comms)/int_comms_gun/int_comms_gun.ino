#include <CRCx.h>
#define BEETLE_ID '1' // change based on beetle
#define ACK_ID '0'
#define HANDSHAKE_ID '1'
#define WAKEUP_ID '2'
#define GUN_ID '3'

#include <IRremote.h>
#include <Wire.h>
#include "constants.h"

IRsend irsend(IR_send_pin);

//global variable to be used for packet and data processing
uint8_t data[16];
uint8_t packet[20];
int seq_num = 0;

//global boolean for handshaking and stop and wait
bool error          = false;
bool handshake      = false;
bool handshake_ack  = false;
unsigned long sent_time;
int activation_count = 0;
bool data_ack       = false;
bool data_sent      = false;

void setup() {
  Serial.begin(115200);
  pinMode(button_pin, INPUT_PULLUP);
  pinMode(13, OUTPUT);
  IrSender.begin(IR_send_pin);
  
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
void data_padding(const char msg[]) {
  for (byte k = 0; k < strlen_P(msg); k++) {
    data[k] = pgm_read_byte_near(msg + k);
  }
}

void packet_overhead(char packet_id) {
  uint8_t result8 = crcx::crc8(data, 16);
  String temp = String(result8, HEX);
  char crc[3];
  temp.toCharArray(crc, 3);
  int j = 0;

  packet[0] = BEETLE_ID;
  packet[1] = packet_id;

  for (int i = 2; i < 18; i = i + 1) {
    packet[i] = data[j];
    j = j + 1;
  }

  if (strlen(crc) == 1) {
    packet[18] = '0';
    packet[19] = crc[0];
  } else {
    packet[18] = crc[0];
    packet[19] = crc[1];
  }
}

void loop() {
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
      case 'W' :
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
        bulletCount = (int)((char)cmd - 'a'); 
        break;
    }
  }

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
      data_padding(ZEROGUN);
    } else if (seq_num == 1) {
      data_padding(ONEGUN);
    }
    packet_overhead(GUN_ID);
    Serial.write((char*)packet, PACKET_SIZE);
    data_sent = true;
    data_ack = false;
    sent_time = millis();
    error = false;
    delay(30);
  }

  if (error && data_sent) {
    if (seq_num == 0) {
      data_padding(ZEROGUN);
    } else if (seq_num == 1) {
      data_padding(ONEGUN);
    }
    packet_overhead(GUN_ID);
    Serial.write((char*)packet, PACKET_SIZE);

    data_ack = false;
    sent_time = millis();
    error = false;
    delay(30);
  }
  buttonState = digitalRead(button_pin);
  if (buttonState == 0) {
    activation_count += 1;
    irsend.sendNEC(0x111111, 32);
    //irsend.sendNEC(0x1111,0x22,true);
    digitalWrite(13, HIGH);
    if(bulletCount <= 0) {
      tone(5,500,600);
      bulletCount -= 1;
    } else {
      tone(5,784,300);
    }
    delay(200);
    digitalWrite(13, LOW);
    delay(300); 
  }
}
