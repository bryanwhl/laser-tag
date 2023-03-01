#include <CRCx.h>
#define BEETLE_ID '0' // change based on beetle
#define HANDSHAKE_ID '1'
#define WAKEUP_ID '2'
#define MOTION_ID '5'
#define MOTION_ID_P1 '5'
#define MOTION_ID_P2 '6'

#include "I2Cdev.h"
#include "MPU6050_6Axis_MotionApps20.h"
#if I2CDEV_IMPLEMENTATION == I2CDEV_ARDUINO_WIRE
#include "Wire.h"
#endif

MPU6050 mpu;
// MPU control/status vars
bool dmpReady = false;  // set true if DMP init was successful
uint8_t mpuIntStatus;   // holds actual interrupt status byte from MPU
uint8_t devStatus;      // return status after each device operation (0 = success, !0 = error)
uint16_t packetSize;    // expected DMP packet size (default is 42 bytes)
uint16_t fifoCount;     // count of all bytes currently in FIFO
uint8_t fifoBuffer[64]; // FIFO storage buffer

// orientation/motion vars
Quaternion q;           // [w, x, y, z]         quaternion container
VectorInt16 aa;         // [x, y, z]            accel sensor measurements
VectorInt16 aaReal;     // [x, y, z]            gravity-free accel sensor measurements
VectorInt16 aaWorld;    // [x, y, z]            world-frame accel sensor measurements
VectorFloat gravity;    // [x, y, z]            gravity vector
float euler[3];         // [psi, theta, phi]    Euler angle container
float ypr[3];           // [yaw, pitch, roll]   yaw/pitch/roll container and gravity vector

//constants
char HANDSHAKE[]  = "HANDSHAKE";
char ACK[]        = "ACK";
char WAKEUP[]     = "WAKEUP";
int PACKET_SIZE   = 20;


//create variable to be used for packet and data processing
uint8_t data[16];
uint8_t packet[20];
float data_set[6];

//boolean checks for logic program
//check that data transfer has begin
//check if receive error or handshake from laptop
bool error          = false;
bool handshake      = false;
bool handshake_ack  = false;
unsigned long TIMEOUT = 1000;
unsigned long sent_time;

void setup() {
  Serial.begin(115200);
#if I2CDEV_IMPLEMENTATION == I2CDEV_ARDUINO_WIRE
  Wire.begin();
  Wire.setClock(400000); // 400kHz I2C clock. Comment this line if having compilation difficulties
#elif I2CDEV_IMPLEMENTATION == I2CDEV_BUILTIN_FASTWIRE
  Fastwire::setup(400, true);
#endif

  mpu.initialize();
  while (!mpu.testConnection()) {
    mpu.initialize();
    delay(10);
  }
  devStatus = mpu.dmpInitialize();
  // supply your own gyro offsets here, scaled for min sensitivity
  mpu.setXGyroOffset(64);
  mpu.setYGyroOffset(-30);
  mpu.setZGyroOffset(-1);
  mpu.setZAccelOffset(2402);
  
  if (devStatus == 0) {
    // Calibration Time: generate offsets and calibrate our MPU6050
    mpu.CalibrateAccel(6);
    mpu.CalibrateGyro(6);
    // turn on the DMP, now that it's ready
    mpu.setDMPEnabled(true);
    // set our DMP Ready flag so the main loop() function knows it's okay to use it
    dmpReady = true;

    // get expected DMP packet size for later comparison
    packetSize = mpu.dmpGetFIFOPacketSize();
  } else {
    // ERROR!
    // 1 = initial memory load failed
    // 2 = DMP configuration updates failed
    // (if it's going to break, usually the code will be 1)
    setup();
  }

  sent_time = millis();
  error = false;
  handshake = false;
  handshake_ack = false;
  delay(100);
}

// count number of digit in data
int countDigits(long num) {
  uint8_t count = 0;
  while (num)
  {
    num = num / 10;
    count++;
  }
  return count;
}

// add digit into string
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

//function to send 1 dataset of motion sensor values string version
void send_data_string(float data_set[]) {
  int signs;
  // convert all value to 5 digit integer
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
  delay(30);

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

  //if dont recieve ACK from laptop, send the next set. Not applicable for motion sensor
  if (millis() - sent_time >= TIMEOUT) {
    error = true;
  }

  if (Serial.available()) {
    byte cmd = Serial.read();
    switch (cmd) {
      case 'A': //Received ACK
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

  delay(30);
  if (handshake && !handshake_ack && error) {
    data_padding(HANDSHAKE);
    packet_overhead(HANDSHAKE_ID);
    Serial.write((char*)packet, PACKET_SIZE);
    sent_time = millis();
    error = false;
  }

  if (!dmpReady) return;
  // read a packet from FIFO
  if (mpu.dmpGetCurrentFIFOPacket(fifoBuffer)) { // Get the Latest packet

    // display Euler angles in degrees
    mpu.dmpGetQuaternion(&q, fifoBuffer);
    mpu.dmpGetGravity(&gravity, &q);
    mpu.dmpGetYawPitchRoll(ypr, &q, &gravity);
    data_set[0] = ypr[2] * 180 / M_PI;
    data_set[1] = ypr[1] * 180 / M_PI;
    data_set[2] = ypr[0] * 180 / M_PI;

    // display real acceleration, adjusted to remove gravity
    mpu.dmpGetQuaternion(&q, fifoBuffer);
    mpu.dmpGetAccel(&aa, fifoBuffer);
    mpu.dmpGetGravity(&gravity, &q);
    mpu.dmpGetLinearAccel(&aaReal, &aa, &gravity);
    data_set[3] = aaReal.x;
    data_set[4] = aaReal.y;
    data_set[5] = aaReal.z;

    //spam sending of data for motion sensor
    if (handshake_ack) {
      send_data_string(data_set);
      memset(data_set, 0, 6);
    }
  }
}
