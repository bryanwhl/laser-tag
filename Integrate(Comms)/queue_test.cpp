#include <iostream>
#include <cstring>
using namespace std;

#define THRESHOLDING_CAPACITY 10
#define ARRAY_SIZE 6
float THRESHOLD_ANGEL = 550;
float THRESHOLD_ACC = 1600;
long DURATION_ACTION_PACKETS = 1500;
long START_ACTION_PACKETS = 0;
bool isStartOfMove = false;

volatile float DIFF_ACC = -1269.0;
volatile float DIFF_YPR = -1269.0;
void print_array(float hehe[6]);

typedef struct Queuee
{
    int front, capacity, size;
    float internalQueue[THRESHOLDING_CAPACITY][ARRAY_SIZE] = {0};
    Queuee()
    {
        front = 0;
        size = 0;
        capacity = THRESHOLDING_CAPACITY;
    }

    bool isFull()
    {
        return size == capacity;
    }

    void queueEnqueue(float data[6])
    {
        if (size >= capacity)
        {
            return;
        }

        int index = (front + size) % THRESHOLDING_CAPACITY;
        ++size;
        memcpy(internalQueue[index], data, ARRAY_SIZE * sizeof(float));
        return;
    }

    void queueDequeue(float data[ARRAY_SIZE])
    {
        if (size == 0)
        {
            return;
        }

        memcpy(data, internalQueue[front], sizeof(internalQueue[front]));
        front = (front + 1) % THRESHOLDING_CAPACITY;
        --size;
        return;
    }

    void getSumOfFirstHalf(float data[6])
    {
        float currentSum[ARRAY_SIZE] = {0, 0, 0, 0, 0, 0};
        int index = (front + 0) % THRESHOLDING_CAPACITY;
        for (int i = 0; i < THRESHOLDING_CAPACITY / 2; ++i)
        {
            index = (front + i) % THRESHOLDING_CAPACITY;
            cout << "index: " << index << '\n';
            for (int j = 0; j < ARRAY_SIZE; ++j)
            {
                currentSum[j] += internalQueue[index][j];
            }
        }
        print_array(currentSum);
        memcpy(data, currentSum, sizeof(currentSum));
    }

    void getSumOfSecondHalf(float data[ARRAY_SIZE])
    {
        float currentSum[ARRAY_SIZE] = {0, 0, 0, 0, 0, 0};
        int index = (front + 0) % THRESHOLDING_CAPACITY;
        for (int i = THRESHOLDING_CAPACITY / 2; i < THRESHOLDING_CAPACITY; ++i)
        {
            index = (front + i) % THRESHOLDING_CAPACITY;
            cout << "index: " << index << '\n';
            for (int j = 0; j < ARRAY_SIZE; ++j)
            {

                currentSum[j] += internalQueue[index][j];
            }
        }
        print_array(currentSum);
        memcpy(data, currentSum, sizeof(currentSum));
    }

    void resetQueue()
    {
        memset(internalQueue, 0, sizeof(internalQueue));
        size = 0;
    }

    void printQueueContent()
    {
        int index = (front + 0) % THRESHOLDING_CAPACITY;
        for (int i = 0; i < size; ++i)
        {
            for (int j = 0; j < ARRAY_SIZE; ++j)
            {
                cout << internalQueue[index][j] << " ";
            }
            index = (index + 1) % THRESHOLDING_CAPACITY;
            cout << "\n";
        }
    }
} Queuee;

Queuee bufffer = Queuee();

bool checkStart0fMove()
{ // 2d array of 20 by 6 dimension
    float differenceAngel = 0;
    float differenceAcc = 0;
    float sumOfFirstHalf[6] = {0, 0, 0, 0, 0, 0};
    float sumOfSecondHalf[6] = {0, 0, 0, 0, 0, 0};

    bufffer.getSumOfFirstHalf(sumOfFirstHalf);
    print_array(sumOfFirstHalf);
    bufffer.getSumOfSecondHalf(sumOfSecondHalf);
    print_array(sumOfSecondHalf);

    for (int i = 0; i < 3; ++i)
    {
        differenceAngel += abs(sumOfFirstHalf[i] - sumOfSecondHalf[i]);
    }
    for (int i = 3; i < 6; ++i)
    {
        differenceAcc += abs(sumOfFirstHalf[i] - sumOfSecondHalf[i]);
    }

    DIFF_ACC = differenceAcc;
    DIFF_YPR = differenceAngel;

    cout << DIFF_YPR << " " << DIFF_ACC << '\n';

    return differenceAcc > THRESHOLD_ACC || differenceAngel > THRESHOLD_ANGEL;
}

void print_array(float hehe[6])
{
    for (int i = 0; i < 6; ++i)
    {
        cout << hehe[i] << ' ';
    }
    cout << '\n';
}

float dummyBuffer[10][6] = {
    {-85.11, -31.78, -34.52, 251, 330, 327},
    {-86.19, -32.37, -34.48, 257, 336, 336},
    {-87.22, -32.87, -34.4, 264, 344, 343},
    {-88.21, -33.29, -34.28, 271, 348, 349},
    {-89.16, -33.63, -34.09, 279, 350, 355},
    {-90.05, -146.06, -33.89, 285, 347, 360},
    {-90.87, -145.82, -33.68, 292, 341, 368},
    {-91.57, -145.64, -33.46, 297, 333, 378},
    {-92.18, -145.51, -33.23, 301, 326, 386},
    {-92.7, -145.44, -33.01, 303, 323, 396},
};

int main()
{
    float dummy_01[6] = {1, 310.39, 120.39, 11.34, 9.09, -9.03};
    float dummy_02[6] = {2, -4.21, -167.0, -410.0, -987.0, 736.0};
    float dummy_03[6] = {3, 27.57, 19.87, -724.0, -628.0, 654.0};
    float dummy_04[6] = {4, 31.45, 13.38, -195.0, -296.0, 440.0};
    float dummy_05[6] = {5, 31.67, 4.87, -949.0, -767.0, 54.0};
    float dummy_06[6] = {6, -30.03, 5.69, 176.0, 501.0, 162.0};
    float dummy_07[6] = {7, -30.46, 17.88, 376.0, 589.0, 271.0};
    float dummy_08[6] = {8, -31.52, 31.75, 603.0, 452.0, 376.0};
    float dummy_09[6] = {9, -31.84, -45.7, 956.0, 802.0, 416.0};
    float dummy_10[6] = {10, -31.01, -58.4, 964.0, 248.0, 372.0};
    bufffer.queueEnqueue(dummyBuffer[0]);
    bufffer.queueEnqueue(dummyBuffer[1]);
    bufffer.queueEnqueue(dummyBuffer[2]);
    bufffer.queueEnqueue(dummyBuffer[3]);
    bufffer.queueEnqueue(dummyBuffer[4]);
    bufffer.queueEnqueue(dummyBuffer[5]);
    bufffer.queueEnqueue(dummyBuffer[6]);
    bufffer.queueEnqueue(dummyBuffer[7]);
    bufffer.queueEnqueue(dummyBuffer[8]);
    bufffer.queueEnqueue(dummyBuffer[9]);
    bufffer.printQueueContent();
    cout << checkStart0fMove() << '\n';
    cout << bufffer.isFull() << '\n';
    return 0;
}

/*
send updated data back to beetle
start of move on beetle
threshold = 10000 (to be tuned)
detect start of move in queue
if start of move -> send all 20 packet in buffer + 30 packet (50 in total)
after 50 packet -> wait for next start of move.

def detect_start_of_move(self): # 2D array of 20 * 6 dimensions
    if len(self.queue) < 20:
        return ''
    move_list = self.queue[:20]
    sum_of_first_10_readings = [0, 0, 0, 0, 0, 0]
    sum_of_next_10_readings = [0, 0, 0, 0, 0, 0]
    for attribute_idx in range(6):
        for reading_no in range(10):
            sum_of_first_10_readings[attribute_idx] += move_list[reading_no][attribute_idx]
        for reading_no in range(10, 20):
            sum_of_next_10_readings[attribute_idx] += move_list[reading_no][attribute_idx]
    difference = 0
    for i in range(6):
        difference += abs(sum_of_first_10_readings[i] - sum_of_next_10_readings[i])
    return difference > THRESHOLD
*/