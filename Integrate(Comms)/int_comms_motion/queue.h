#ifndef QUEUE_H
#define QUEUE_H
#define THRESHOLDING_CAPACITY 10
#define ARRAY_SIZE 6

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
      index = (front + i) % THRESHOLDING_CAPACITY;
      for (int j = 0; j < ARRAY_SIZE; ++j) {
        currentSum[j] += internalQueue[index][j];
      }
    }
    memcpy(data, currentSum, sizeof(currentSum));
  }

  void getSumOfSecondHalf(float data[ARRAY_SIZE]) {
    float currentSum[ARRAY_SIZE] = {0, 0, 0, 0, 0, 0};
    int index = (front + 0) % THRESHOLDING_CAPACITY;
    for (int i = THRESHOLDING_CAPACITY / 2; i < THRESHOLDING_CAPACITY; ++i) {
      index = (front + i) % THRESHOLDING_CAPACITY;
      for (int j = 0; j < ARRAY_SIZE; ++j) {

        currentSum[j] += internalQueue[index][j];
      }
    }
    memcpy(data, currentSum, sizeof(currentSum));
  }

  void resetQueue() {
    memset( internalQueue, 0, sizeof(internalQueue) );
    size = 0;
  }
} Queuee;

#endif
