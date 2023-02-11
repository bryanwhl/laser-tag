#include <CRCx.h>
#define BEETLE_ID '0' // change based on beetle
#define ACK_ID '0'
#define HANDSHAKE_ID '1'
#define WAKEUP_ID '2'
#define GUN_ID '3'
#define VEST_ID '4'
#define MOTION_ID '5'
#define MOTION_ID_P1 '5'
#define MOTION_ID_P2 '6'
// uncomment the system that bluno will be used in
//#define isGUN
//#define isVEST
#define isMOTION


char HANDSHAKE[] = "HANDSHAKE";
char ACK[] = "ACK";
char WAKEUP[] = "WAKEUP";
char GUN[] = "GUN";
char VEST[] = "VEST";
int PACKET_SIZE = 20;


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
bool data_ack = false;
bool data_sent = false;
String time;
unsigned long time_out = 1000;
volatile int activation_count = 3;

void setup() {
  Serial.begin(115200);
  error = false;
  handshake = false;
  handshake_ack = false;
  data_ack = false;
  while (!Serial) {
  }
  delay(1000);
}

int countDigits(long num) {
  uint8_t count = 0;
  while (num)
  {
    num = num / 10;
    count++;
  }
  return count;
}

void insert_digit(char temp_data[16], int &index, long value) {
  int num_digit;
  char holder[6];
  String temp;

  temp = String(abs(value));
  temp.toCharArray(holder, 6);
  num_digit = countDigits(abs(value));
  for (int i = 0; i < 5 - num_digit; ++i) {
    temp_data[index++] = '0';
  }
  for (int i = 0; i < num_digit; ++i) {
    temp_data[index++] = holder[i];
  }
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

  //packet[19] = crc_8(data, 16);

  //*
  // add crc to last 2 bit of packet
  if (strlen(crc) == 1) {
    packet[18] = '0';
    packet[19] = crc[0];
  } else {
    packet[18] = crc[0];
    packet[19] = crc[1];
  }//*/
}

//function to send 1 dataset of motion sensor values byte version
void send_data_bytes(float data_set[]) {
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
  Serial.write((uint8_t *)(packet), sizeof(packet));
  memset(data, 0, 16);
  delay(80);
}

//function to send 1 dataset of motion sensor values string version
void send_data_string(float data_set[]) {
  int signs;
  long roll  =  (long)(data_set[0] * 100) % 100000;
  long pitch =  (long)(data_set[1] * 100) % 100000;
  long yaw   =  (long)(data_set[2] * 100) % 100000;
  long accX  =  (long)(data_set[3] * 100) % 100000;
  long accY  =  (long)(data_set[4] * 100) % 100000;
  long accZ  =  (long)(data_set[5] * 100) % 100000;
  int index;
  char sign[2];
  char temp_data[16];

  //packet 0
  signs = 0;
  index = 1;
  for (int i = 0; i < 3; ++i) {
    if (data_set[i] < 0) {
      signs += 1;
    }
    signs *= 2;
  }
  String(signs).toCharArray(sign, 2);
  temp_data[0] = sign[0];

  insert_digit(temp_data, index, roll);
  insert_digit(temp_data, index, pitch);
  insert_digit(temp_data, index, yaw);

  data_padding(temp_data);
  packet_overhead(MOTION_ID_P1);
  Serial.write((char*)packet, PACKET_SIZE);
  memset(data, 0, 16);
  delay(90);

  //packet 1
  signs = 0;
  index = 1;
  for (int i = 0; i < 3; ++i) {
    signs *= 2;
    if (data_set[i + 3] < 0) {
      signs += 1;
    }
  }
  String(signs).toCharArray(sign, 2);
  temp_data[0] = sign[0];

  insert_digit(temp_data, index, accX);
  insert_digit(temp_data, index, accY);
  insert_digit(temp_data, index, accZ);

  data_padding(temp_data);
  packet_overhead(MOTION_ID_P2);
  Serial.write((char*)packet, 20);
  memset(data, 0, 16);
}


void loop() {
  
  //* This is for dummy data
  start = 0;
  memset(data_set, 0, 6);
  data_set[0] = roll[start];
  data_set[1] = pitch[start];
  data_set[2] = yaw[start];
  data_set[3] = AccX[start];
  data_set[4] = AccY[start];
  data_set[5] = AccZ[start];
  //*/


  //if dont recieve ACK from laptop, send the next set
  if (millis() < time_out) {
    error = true;
  }
  if (Serial.available()) {
    byte cmd = Serial.read();
    switch (cmd) {
      case 'A': //Received ACK
        data_ack = true;
        if (handshake) {
          handshake_ack = true;
          handshake = false;
          delay(1000);
        }
        if(handshake_ack) {
          data_sent = false;
          error = false;
        }
        break;
      case 'H'://Received Handshake request
        data_padding(HANDSHAKE);
        packet_overhead(HANDSHAKE_ID);
        Serial.write((char*)packet, PACKET_SIZE);
        memset(data, 0, 16);

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
        Serial.write((char*)packet, PACKET_SIZE);
        memset(data, 0, 16);
        break;
      default:break;
    }
  }

  delay(90);

  #ifdef isMOTION
  if (handshake_ack) {
    send_data_string(data_set);

    //handshake_ack = false;
    //handshake = false;
  }
  #endif

  if(data_ack && handshake_ack && activation_count > 0){
    #ifdef isGUN
    data_padding(GUN);
    packet_overhead(GUN_ID);
    Serial.write((char*)packet, PACKET_SIZE);
    #endif

    #ifdef isVEST
    data_padding(VEST);
    packet_overhead(VEST_ID);
    Serial.write((char*)packet, PACKET_SIZE);
    #endif
    data_sent = true;
    data_ack = false;
  }

  if(error && data_sent){
    #ifdef isGUN
    data_padding(GUN);
    packet_overhead(GUN_ID);
    Serial.write((char*)packet, PACKET_SIZE);
    #endif

    #ifdef isVEST
    data_padding(VEST);
    packet_overhead(VEST_ID);
    Serial.write((char*)packet, PACKET_SIZE);
    #endif

    data_ack = false;
    error = false;
  }
}
