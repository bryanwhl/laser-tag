#include <iostream>
#include <cstring>
using namespace std;

#define QUEUE_CAPACITY 20
#define ARRAY_SIZE 6
float THRESHOLD = 10000 * 100;
float NUM_ACTION_PACKETS = 50;

bool startOfMove = false;

struct Queuee {
    int front, capacity, size;
    float internalQueue[QUEUE_CAPACITY][ARRAY_SIZE];
    Queuee() {
        front = 0;
        size = 0;
        capacity = QUEUE_CAPACITY;
    }
 
    void queueEnqueue(float data[6]) {
        if (size >= capacity) {
            return;
        }
         
        int index = (front+size) % 20;
        ++size;
        memcpy(internalQueue[index], data, ARRAY_SIZE * sizeof(float));
        return;
    }
 
    void queueDequeue(float data[ARRAY_SIZE]) {
        if (size == 0) {
            return;
        }
        
        memcpy(data, internalQueue[front], sizeof(internalQueue[front]));
        front = (front+1) % 20;
        --size;
        return;
    }
    
    void getSumOfFirstHalf(float data[6]) {
        float currentSum[ARRAY_SIZE] = {0, 0, 0, 0, 0, 0};
	int index = (front + 0) % 20;
        for(int i = 0; i < 10; ++i) {
            for(int j = 0; j < ARRAY_SIZE; ++j) {
                currentSum[j] += internalQueue[index][j];
            }
	    ++index;
        }
        memcpy(data, currentSum, sizeof(currentSum));
    }
    
    void getSumOfSecondHalf(float data[ARRAY_SIZE]) {
        float currentSum[ARRAY_SIZE] = {0, 0, 0, 0, 0, 0};
	int index = (front + 0) % 20;
        for(int i = 10; i < 20; ++i) {
            for(int j = 0; j < ARRAY_SIZE; ++j) {
                index = (front + i) % 20;
                currentSum[j] += internalQueue[index][j];
            }
	    ++index;
        }
        memcpy(data, currentSum, sizeof(currentSum));
    }

    void printQueueContent() {
      int index = (front + 0) % 20;
      for(int i = 0; i < size; ++i){
        for(int j = 0; j < ARRAY_SIZE; ++j){
          cout << internalQueue[index][j] << " ";
        }
        index = (index+1)%20;
        cout << "\n";
      }
    }
};    

Queuee buffer;

bool checkStart0fMove() { //2d array of 20 by 6 dimension
    float difference = 0;
    float sumOfFirstHalf[6] = {0, 0, 0, 0, 0, 0};
    float sumOfSecondHalf[6] = {0, 0, 0, 0, 0, 0};
    
    buffer.getSumOfFirstHalf(sumOfFirstHalf);
    buffer.getSumOfSecondHalf(sumOfSecondHalf);
    
    for(int i = 0; i < 6; ++i) {
        difference += abs(sumOfFirstHalf[i] - sumOfSecondHalf[i]);
    }
    return (long)difference > THRESHOLD;
}

void print_array(float hehe[6]) {
    for(int i = 0; i < 6; ++i){
        cout << hehe[i] << ' ';
    }
    cout << '\n';
}

int main(){
	float dummy_01[6] = {1, 310.39, 120.39, 11.34, 9.09, -9.03};
    float dummy_02[6] = {2,-4.21,-167.0,-410.0,-987.0,736.0};
    float dummy_03[6] = {3,27.57,19.87,-724.0,-628.0,654.0};
    float dummy_04[6] = {4,31.45,13.38,-195.0,-296.0,440.0};
    float dummy_05[6] = {5,31.67,4.87,-949.0,-767.0,54.0};
    float dummy_06[6] = {6,-30.03,5.69,176.0,501.0,162.0};
    float dummy_07[6] = {7,-30.46,17.88,376.0,589.0,271.0};
    float dummy_08[6] = {8,-31.52,31.75,603.0,452.0,376.0};
    float dummy_09[6] = {9,-31.84,-45.7,956.0,802.0,416.0};
    float dummy_10[6] = {10,-31.01,-58.4,964.0,248.0,372.0};
    float dummy_11[6] = {11,-29.38,-69.89,522.0,284.0,411.0};
    float dummy_12[6] = {12,-27.78,-80.55,911.0,76.0,653.0};
    float dummy_13[6] = {13,-25.82,-91.1,-554.0,-191.0,328.0};
    float dummy_14[6] = {14,-24.14,-101.58,-640.0,-158.0,171.0};
    float dummy_15[6] = {15,-22.91,-111.85,-836.0,-316.0,302.0};
    float dummy_16[6] = {16,-22.52,-121.51,-760.0,-337.0,760.0};
    float dummy_17[6] = {17,-22.16,-130.84,-7.0,-318.0,434.0};
    float dummy_18[6] = {18,-21.8,-139.87,-879.0,-908.0,119.0};
    float dummy_19[6] = {19,-21.93,-148.1,-872.0,-483.0,763.0};
    float dummy_20[6] = {20,-22.65,-155.69,-733.0,-100.0,682.0};
	buffer.queueEnqueue(dummy_01);
    buffer.queueEnqueue(dummy_02);
    buffer.queueEnqueue(dummy_03);
    buffer.queueEnqueue(dummy_04);
    buffer.queueEnqueue(dummy_05);
    buffer.queueEnqueue(dummy_06);
    buffer.queueEnqueue(dummy_07);
    buffer.queueEnqueue(dummy_08);
    buffer.queueEnqueue(dummy_09);
    buffer.queueEnqueue(dummy_10);
    buffer.queueEnqueue(dummy_11);
    buffer.queueEnqueue(dummy_12);
    buffer.queueEnqueue(dummy_13);
    buffer.queueEnqueue(dummy_14);
    buffer.queueEnqueue(dummy_15);
    buffer.queueEnqueue(dummy_16);
    buffer.queueEnqueue(dummy_17);
    buffer.queueEnqueue(dummy_18);
    buffer.queueEnqueue(dummy_19);
    buffer.queueEnqueue(dummy_20);
    buffer.queueDequeue(dummy_01);
    buffer.queueDequeue(dummy_02);
    buffer.queueDequeue(dummy_03);
    buffer.queueDequeue(dummy_04);
    buffer.queueEnqueue(dummy_01);
    buffer.queueEnqueue(dummy_02);
    buffer.queueEnqueue(dummy_03);
    buffer.queueEnqueue(dummy_04);
    buffer.queueEnqueue(dummy_04);
    buffer.queueEnqueue(dummy_04);
    buffer.queueEnqueue(dummy_04);
    buffer.queueEnqueue(dummy_04);
    buffer.printQueueContent();
    cout << checkStart0fMove() << '\n';
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