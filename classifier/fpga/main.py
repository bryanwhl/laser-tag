# from fpga import FPGA
from parse import Parser
from start_of_move import detect_start_of_move
import time

BITFILE_PATH = "./final.bit"

WINDOW_SIZE = 20
INT_TO_ACTION_MAPPING = {
    0: 'grenade',
    1: 'shield',
    2: 'reload',
    3: 'logout',
    4: 'nil'
}

motionOneQueue = [] # 2D array of 6 columns

if __name__ == "__main__":
    
    # fpga = FPGA(BITFILE_PATH)
    for i in range(10):
        motionOneQueue.append([1,2,3,4,5,6])

    for i in range(10, 20):
        motionOneQueue.append([2,3,4,5,6,7])

    # Parser.test_parser(motionOneQueue, WINDOW_SIZE)
    print(detect_start_of_move(motionOneQueue[:20]))

    # while True:
    #     if len(motionOneQueue) < 20:
    #         time.sleep(1)
    #         continue
    #     Parser.obtain_data_for_start_of_move(motionOneQueue, WINDOW_SIZE)
        
        
