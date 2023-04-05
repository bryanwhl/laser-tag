#ifndef CONSTANTS_H
#define CONSTANTS_H

int bulletCount = 6;
int buttonState = 1;
static const int IR_send_pin = 3;
static const int button_pin = A2;

//constants
static const char HANDSHAKE[] PROGMEM = "#######HANDSHAKE";
static const char ACK[]       PROGMEM = "#############ACK";
static const char WAKEUP[]    PROGMEM = "##########WAKEUP";
static const char ZEROGUN[]   PROGMEM = "############0GUN";
static const char ONEGUN[]    PROGMEM = "############1GUN";
static const int PACKET_SIZE  PROGMEM = 20;
const unsigned long TIMEOUT = 1000;

#endif
