#include <CRCx.h>
#define BEETLE_ID '0'
#define ACK_ID '0'
#define HANDSHAKE_ID '1'
#define GUN_ID '2'
#define VEST_ID '3'
#define MOTION_ID '4'
#define WAKEUP_ID '5'

char HANDSHAKE[] = "HANDSHAKE";
char ACK[] = "ACK";
char WAKEUP[] = "WAKEUP";
char GUN[] = "GUN";
char VEST[] = "VEST";


//create variable to be used for packet and data processing
uint8_t data[16];
uint8_t packet[20];
float data_set[6];

//dummy to test
int start = 0;
float roll[] = {222.14, 222.30, 222.12, 221.88, 221.73};    //3byte
float pitch[] = {273.05, 272.90, 272.91, 272.93, 272.95};   //3byte
float yaw[] = {370.27, -370.24, -370.29, -370.37, -370.49}; //3byte
float AccX[] = { -0.48, 0.47, 0.46, 0.46, 0.46};            //2byte
float AccY[] = { -0.15, -0.13, -0.16, -0.20, -0.22};        //2byte
float AccZ[] = {1, 2, 3, 4, 5};                             //2byte
//1byte for signs of all 6 variable

//boolean checks for logic program
//check that data transfer has begin
//check if receive error or handshake from laptop
bool error = false;
bool handshake = false;
bool handshake_ack = false;
String time;
unsigned long time_out = 99999999;



void setup() {
  Serial.begin(115200);
  while (!Serial) {
  }
  delay(1000);
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
  }
}

//function to send 1 dataset of motion sensor values
void send_data(float data_set[]) {
  unsigned int x;
  uint8_t xlow ;
  uint8_t xhigh ;
  uint8_t signs = 0;
  //roll, pitch and yaw
  for (int i = 0; i < 3; ++i) {
    x = abs( (int)data_set[i] );
    xlow = x & 0xff;
    xhigh  = (x >> 8);
    data[0 + i * 3] = xlow;
    data[1 + i * 3] = xhigh;
    data[2 + i * 3] = abs((int)(data_set[i] * 100) % 100);
    if (data_set[i] < 0) {
      signs + 1;
    }
    signs *= 2;
  }
  //x, y, z
  for (int i = 0; i < 3; ++i) {
    data[9 + i * 2] = abs( (int)data_set[i + 3] );
    data[10 + i * 2] = abs((int)(data_set[i + 3] * 100) % 100) ;
  }

  packet_overhead(MOTION_ID);
  Serial.write((char*)packet);
  Serial.flush();
  memset(data, 0, 17);
  delay(20);
}


void loop() {
  //* This is for dummy data
  data_set[0] = roll[start];
  data_set[1] = pitch[start];
  data_set[2] = yaw[start];
  data_set[3] = AccX[start];
  data_set[4] = AccY[start];
  data_set[5] = AccZ[start];
  start = 4 ? 0 : start + 1;
  //*/

  
  //if dont recieve ACK from laptop, send the next set
  if (millis() < time_out) {
    error = true;
  }
  if (Serial.available()) {
    byte cmd = Serial.read();
    switch (cmd) {
      case 'A': //Received ACK
        data_padding(ACK);
        packet_overhead(ACK_ID);
        Serial.write((char*)packet);
        Serial.flush();
        memset(data, 0, 17);

        if (handshake) {
          error = false;
          handshake_ack = true;
        }
        break;
      case 'H'://Received Handshake request
        data_padding(HANDSHAKE);
        packet_overhead(HANDSHAKE_ID);
        Serial.write((char*)packet);
        Serial.flush();
        memset(data, 0, 17);

        //Reset all boolean to default
        error = false;
        handshake = true;
        handshake_ack = false;
        break;
      case 'N': // Receive Nack
        error = true;
        break;
      case 'W' ://Received Wakeup Call
        data_padding(ACK);
        packet_overhead(ACK_ID);
        Serial.write((char*)packet);
        Serial.flush();
        memset(data, 0, 17);
    }
    /*

      //if dance start send 1 dataset in 3 packets. if issue with any 3, resend packet. if error more than 3 skip current data set.
      if (dance_start && handshake_confirmed) {
      //if one of the 3 packets have issue resend all 3 again.
      if (error) {
        if (error_num > 2) {
          next_set = true;
          error_num = 0;
        } else {
          //Send data set as part of resolving error
          data_set[0] = convert_2dp(roll[err_set]);
          data_set[1] = convert_2dp(pitch[err_set]);
          data_set[2] = convert_2dp(yaw[err_set]);
          data_set[3] = convert_2dp(AccX[err_set]);
          data_set[4] = convert_2dp(AccY[err_set]);
          data_set[5] = convert_2dp(AccZ[err_set]);
          //Call function to send data_set
          dance_data(data_set);
          error_num++;
        }
        error = false;
      }
           data_started = true;
           //Only send next set if ack or err received
           if (next_set) {
             //prepare all data in to single array
             time_out = millis() + 1000;
             err_set = current_set;
             data_set[0] = convert_2dp(roll[current_set]);
             data_set[1] = convert_2dp(pitch[current_set]);
             data_set[2] = convert_2dp(yaw[current_set]);
             data_set[3] = convert_2dp(AccX[current_set]);
             data_set[4] = convert_2dp(AccY[current_set]);
             data_set[5] = convert_2dp(AccZ[current_set]);
             //Call function to send data_set
             dance_data(data_set);
             //loop dummy data
             if (current_set != 4) {
               current_set++;
             } else {
               current_set = 0;
             }
             next_set = false;
           }

      }//*/
  }
  delay(100);
}
