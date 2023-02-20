#include <CRCx.h>
#define BEETLE_ID '1' // change based on beetle
#define HANDSHAKE_ID '1'
#define WAKEUP_ID '2'
#define GUN_ID '3'

#include <IRremote.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <Fonts/FreeSans12pt7b.h>

#define SCREEN_WIDTH 128 // OLED display width, in pixels
#define SCREEN_HEIGHT 64 // OLED display height, in pixels
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);
int bulletCount = 6;
int buttonState = 1;
static const int IR_send_pin = 3;
static const int button_pin = A2;
IRsend irsend(IR_send_pin);

//constants
static const char HANDSHAKE[] PROGMEM = "#######HANDSHAKE";
static const char ACK[]       PROGMEM = "#############ACK";
static const char WAKEUP[]    PROGMEM = "##########WAKEUP";
static const char ZEROGUN[]   PROGMEM = "############0GUN";
static const char ONEGUN[]    PROGMEM = "############1GUN";
static const int PACKET_SIZE  PROGMEM = 20;


//create variable to be used for packet and data processing
uint8_t data[16];
uint8_t packet[20];
int seq_num = 0;

//boolean checks for logic program
//check that data transfer has begin
//check if receive error or handshake from laptop
bool error          = false;
bool handshake      = false;
bool handshake_ack  = false;
bool data_ack       = false;
bool data_sent      = false;
const unsigned long TIMEOUT = 1000;
unsigned long sent_time;
int activation_count = 0;

void setup() {
  Serial.begin(115200);
  pinMode(button_pin, INPUT_PULLUP);
  pinMode(13, OUTPUT);
  IrSender.begin(IR_send_pin);

  /*
  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) { // Address 0x3D for 128x64
    Serial.println(F("SSD1306 allocation failed"));
    for (;;);
  }
  display.clearDisplay();
  display.setFont(&FreeSans12pt7b);
  display.setTextSize(1);
  display.setTextColor(WHITE);
  display.setCursor(0, 10);
  display.println("Ready");
  display.display(); //*/

  
  sent_time = millis();
  error = false;
  handshake = false;
  handshake_ack = false;
  data_ack = false;
  data_sent = false;
  seq_num = 0;
  while (!Serial) {
  }
  delay(100);
}

//Add # to pad string to 16 char.
void data_padding(char msg[]) {
  for (byte k = 0; k < strlen_P(msg); k++) {
    data[k] = pgm_read_byte_near(msg + k);
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
      default: break;
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

    /*
    display.clearDisplay();
    display.setCursor(30, 30);
    display.println("Bang!");
    display.display();
    irsend.sendNEC(0x111111, 32);
    //irsend.sendNEC(0x1111,0x22,true); //*/
    digitalWrite(13, HIGH);
    bulletCount -= 1;
    if (bulletCount <= 0) {
      bulletCount = 6;
    }
    delay(500);
    /*
    display.clearDisplay();
    display.setCursor(30, 30);
    display.println(bulletCount);
    display.display();
    digitalWrite(13, LOW); //*/
  }
}
