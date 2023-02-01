#include <CRCx.h>
#define beetle_id 0

int seq = 0;
int vest_packet[10] = {-1};
char h_msg[] = "HANDSHAKE";
char a_msg[] = "ACK";
//create variable to be used for packet and data processing
char temp_msg[17];
uint8_t data[17];
uint8_t packet[21];

void setup() {
  Serial.begin(115200);
  int handshaking[10] = {-1};
  handshaking[0] = ACKNOWLEDGE;
  while (true) {
    if (Serial.available() && Serial.read() == 'H') {
      Serial.write(char*(handshaking));
      while (true) {
        if (Serial.available() && Serial.read() == 'A') {
          break;
        }
      }
      break;
    }
    delay(100);
  }
}

uint16_t checksumCalculator(uint8_t * data, uint16_t length)
{
   uint16_t curr_crc = 0x0000;
   uint8_t sum1 = (uint8_t) curr_crc;
   uint8_t sum2 = (uint8_t) (curr_crc >> 8);
   int index;
   for(index = 0; index < length; index = index+1)
   {
      sum1 = (sum1 + data[index]) % 255;
      sum2 = (sum2 + sum1) % 255;
   }
   return (sum2 << 8) | sum1;
}

void loop() {
  // Below is stop and wait prototype
  vest_packet[0] = VEST;
  vest.seq_id = beetle_id + seq * 10;
  Serial.print("Reached here");
  Serial.write( (byte*)&vest, sizeof(vest));
  while (true) {
    if (Serial.available()) {
      if (Serial.read() == 'A') {
        seq = 0 ? 1 : 0;
        break;
      } else if (Serial.read() == 'N') {
        Serial.write( (byte*)&vest, sizeof(vest));
      }
    }
    delay(100);
  }
}
