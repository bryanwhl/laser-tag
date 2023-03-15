#include <CRCx.h>
#define BEETLE_ID '0' // change based on beetle
#define HANDSHAKE_ID '1'
#define WAKEUP_ID '2'
#define MOTION_ID_P1 '5'
#define MOTION_ID_P2 '6'

#include "I2Cdev.h"
#include "MPU6050_6Axis_MotionApps20.h"
#if I2CDEV_IMPLEMENTATION == I2CDEV_ARDUINO_WIRE
#include "Wire.h"
#endif

MPU6050 mpu;
// MPU control/status vars
uint8_t mpuIntStatus;   // holds actual interrupt status byte from MPU
uint8_t devStatus;      // return status after each device operation (0 = success, !0 = hasError)
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
float dataSet[6];

//boolean checks for logic program
//check that data transfer has begin
//check if receive error or handshake from laptop
bool hasError          = false;
bool hasHandshake      = false;
bool hasHandshakeAck  = false;
unsigned long TIMEOUT = 1000;
unsigned long sentTime;

/*-------------------------------------------------------------------------------------
  START OF THRESHOLDING (BRYAN)
  -------------------------------------------------------------------------------------*/
#define THRESHOLDING_CAPACITY 10
#define ARRAY_SIZE 6
float THRESHOLD_ANGEL = 230;
float THRESHOLD_ACC = 2200;
long DURATION_ACTION_PACKETS = 2000;
long START_ACTION_PACKETS = 0;
bool isStartOfMove = false;

volatile float DIFF_ACC = -1269.0;
volatile float DIFF_YPR = -1269.0;

typedef struct Queuee {
  int front, capacity, size;
  float internalQueue[THRESHOLDING_CAPACITY][ARRAY_SIZE] = {0};
  Queuee() {
    front = 0;
    size = 0;
    capacity = THRESHOLDING_CAPACITY;
  }

  bool isFull() {
    return size == capacity;
  }

  void queueEnqueue(float data[6]) {
    if (size >= capacity) {
      return;
    }

    int index = (front + size) % THRESHOLDING_CAPACITY;
    ++size;
    memcpy(internalQueue[index], data, ARRAY_SIZE * sizeof(float));
    return;
  }

  void queueDequeue(float data[ARRAY_SIZE]) {
    if (size == 0) {
      return;
    }

    memcpy(data, internalQueue[front], sizeof(internalQueue[front]));
    front = (front + 1) % THRESHOLDING_CAPACITY;
    --size;
    return;
  }

  void getSumOfFirstHalf(float data[6]) {
    float currentSum[ARRAY_SIZE] = {0, 0, 0, 0, 0, 0};
    int index = (front + 0) % THRESHOLDING_CAPACITY;
    for (int i = 0; i < THRESHOLDING_CAPACITY / 2; ++i) {
      for (int j = 0; j < ARRAY_SIZE; ++j) {
        currentSum[j] += internalQueue[index][j];
      }
      index = (front + i) % THRESHOLDING_CAPACITY;
    }
    memcpy(data, currentSum, sizeof(currentSum));
  }

  void getSumOfSecondHalf(float data[ARRAY_SIZE]) {
    float currentSum[ARRAY_SIZE] = {0, 0, 0, 0, 0, 0};
    int index = (front + 0) % THRESHOLDING_CAPACITY;
    for (int i = THRESHOLDING_CAPACITY / 2; i < THRESHOLDING_CAPACITY; ++i) {
      for (int j = 0; j < ARRAY_SIZE; ++j) {

        currentSum[j] += internalQueue[index][j];
      }
      index = (front + i) % THRESHOLDING_CAPACITY;
    }
    memcpy(data, currentSum, sizeof(currentSum));
  }

  void resetQueue() {
    memset( internalQueue, 0, sizeof(internalQueue) );
    size = 0;
  }
} Queuee;

Queuee bufffer = Queuee();

bool checkStart0fMove() { //2d array of 20 by 6 dimension
  float differenceAngel = 0;
  float differenceAcc = 0;
  float sumOfFirstHalf[6] = {0, 0, 0, 0, 0, 0};
  float sumOfSecondHalf[6] = {0, 0, 0, 0, 0, 0};

  bufffer.getSumOfFirstHalf(sumOfFirstHalf);
  bufffer.getSumOfSecondHalf(sumOfSecondHalf);

  for (int i = 0; i < 3; ++i) {
    differenceAngel += abs(sumOfFirstHalf[i] - sumOfSecondHalf[i]);
  }
  for (int i = 3; i < 6; ++i) {
    differenceAcc += abs(sumOfFirstHalf[i] - sumOfSecondHalf[i]);
  }

  DIFF_ACC = differenceAcc;
  DIFF_YPR = differenceAngel;


  return differenceAcc > THRESHOLD_ACC || differenceAngel > THRESHOLD_ANGEL;
}

/*-------------------------------------------------------------------------------------
  END OF THRESHOLDING
  -------------------------------------------------------------------------------------*/

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

    // get expected DMP packet size for later comparison
    packetSize = mpu.dmpGetFIFOPacketSize();
  } else {
    // hasERROR!
    // 1 = initial memory load failed
    // 2 = DMP configuration updates failed
    // (if it's going to break, usually the code will be 1)
    setup();
  }

  sentTime = millis();
  hasError = false;
  hasHandshake = false;
  hasHandshakeAck = false;
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
void insertDigit(char tempData[16], int &index, long value) {
  int numDigit;
  char holder[6];
  String temp;

  temp = String(abs(value));
  temp.toCharArray(holder, 6);
  numDigit = countDigits(abs(value));
  for (int i = 0; i < 5 - numDigit; ++i) {
    tempData[index++] = '0';
  }
  for (int i = 0; i < numDigit; ++i) {
    tempData[index++] = holder[i];
  }
}

//Add # to pad string to 16 char.
void dataPadding(char msg[]) {
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
void packetOverhead(char packetId) {
  uint8_t result8 = crcx::crc8(data, 16);
  String temp = String(result8, HEX);
  char crc[3];
  temp.toCharArray(crc, 3);
  int j = 0;

  //heading for packet
  packet[0] = BEETLE_ID;
  packet[1] = packetId;

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
void sendDataString(float dataSet0, float dataSet1, float dataSet2, float dataSet3, float dataSet4, float dataSet5) {
  int signs;
  // convert all value to 5 digit integer
  long roll  =  (long)(dataSet0 * 100) % 100000;
  long pitch =  (long)(dataSet1 * 100) % 100000;
  long yaw   =  (long)(dataSet2 * 100) % 100000;
  long accX  =  (long)(dataSet3 * 100) % 100000;
  long accY  =  (long)(dataSet4 * 100) % 100000;
  long accZ  =  (long)(dataSet5 * 100) % 100000;

  int index;
  char sign[2];
  char tempData[16];

  //packet 0
  signs = 0;
  index = 1;
  for (int i = 0; i < 3; ++i) {
    if (dataSet[i] < 0) {
      signs += 1;
    }
    signs *= 2;
  }
  String(signs).toCharArray(sign, 2);
  tempData[0] = sign[0];

  insertDigit(tempData, index, roll);
  insertDigit(tempData, index, pitch);
  insertDigit(tempData, index, yaw);
  dataPadding(tempData);
  packetOverhead(MOTION_ID_P1);
  Serial.write((char*)packet, PACKET_SIZE);
  memset(data, 0, 16);

  delay(40);

  //packet 1
  signs = 0;
  index = 1;
  for (int i = 0; i < 3; ++i) {
    signs *= 2;
    if (dataSet[i + 3] < 0) {
      signs += 1;
    }
  }
  String(signs).toCharArray(sign, 2);
  tempData[0] = sign[0];

  insertDigit(tempData, index, accX);
  insertDigit(tempData, index, accY);
  insertDigit(tempData, index, accZ);

  dataPadding(tempData);
  packetOverhead(MOTION_ID_P2);
  Serial.write((char*)packet, 20);
  memset(data, 0, 16);
}


void loop() {

  //if dont recieve ACK from laptop, send the next set. Not applicable for motion sensor
  if (millis() - sentTime >= TIMEOUT) {
    hasError = true;
  }

  if (Serial.available()) {
    byte cmd = Serial.read();
    switch (cmd) {
      case 'A': //Received ACK
        if (hasHandshake) {
          hasHandshakeAck = true;
          hasHandshake = false;
          delay(100);
        }
        break;
      case 'H'://Received Handshake request
        dataPadding(HANDSHAKE);
        packetOverhead(HANDSHAKE_ID);
        Serial.write((char*)packet, PACKET_SIZE);
        memset(data, 0, 16);
        sentTime = millis();
        hasHandshake = true;

        //Reset all boolean to default since hasHandshake req is only when connecting/reconnecting
        hasError = false;
        hasHandshakeAck = false;
        break;
      case 'W' ://Received Wakeup Call
        dataPadding(WAKEUP);
        packetOverhead(WAKEUP_ID);
        Serial.write((char*)packet, PACKET_SIZE);
        memset(data, 0, 16);
        break;
      default: break;
    }
  }

  if (hasHandshake && !hasHandshakeAck && hasError) {
    dataPadding(HANDSHAKE);
    packetOverhead(HANDSHAKE_ID);
    Serial.write((char*)packet, PACKET_SIZE);
    sentTime = millis();
    hasError = false;
  }

  // read a packet from FIFO
  if (mpu.dmpGetCurrentFIFOPacket(fifoBuffer)) { // Get the Latest packet

    // display Euler angles in degrees
    mpu.dmpGetQuaternion(&q, fifoBuffer);
    mpu.dmpGetGravity(&gravity, &q);
    mpu.dmpGetYawPitchRoll(ypr, &q, &gravity);
    dataSet[0] = ypr[2] * 180 / M_PI;
    dataSet[1] = ypr[1] * 180 / M_PI;
    dataSet[2] = ypr[0] * 180 / M_PI;

    // display real acceleration, adjusted to remove gravity
    mpu.dmpGetQuaternion(&q, fifoBuffer);
    mpu.dmpGetAccel(&aa, fifoBuffer);
    mpu.dmpGetGravity(&gravity, &q);
    mpu.dmpGetLinearAccel(&aaReal, &aa, &gravity);
    dataSet[3] = aaReal.x / 100;
    dataSet[4] = aaReal.y / 100;
    dataSet[5] = aaReal.z / 100;

    //spam sending of data for motion sensor
    if (hasHandshakeAck) {
      //if (true) {
      bufffer.queueEnqueue(dataSet);

      if (bufffer.isFull() && !isStartOfMove) {
        isStartOfMove = checkStart0fMove();
        if (isStartOfMove) {
          START_ACTION_PACKETS = millis();
        }
        /*
          Serial.print(DIFF_ACC);
          Serial.print("--");
          Serial.println(DIFF_YPR);//*/
        bufffer.queueDequeue(dataSet);
      }
      if (bufffer.isFull() && isStartOfMove) {

        bufffer.queueDequeue(dataSet);
        sendDataString(dataSet[0], dataSet[1], dataSet[2], dataSet[3], dataSet[4], dataSet[5]);
        //memset(dataSet, 0, 6);
        if ( (millis() - START_ACTION_PACKETS) >= DURATION_ACTION_PACKETS ) {
          bufffer.resetQueue();
          isStartOfMove = false;
          delay(1000);
        }
      }
    }
  }
}
