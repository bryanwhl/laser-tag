# from pynq import Overlay
# from pynq import allocate

# import pynq.lib.dma
# from pynq import DefaultIP
import random

import time

import numpy as np
from parse import Parser
from struct import unpack, pack

BITFILE_PATH = "./final.bit"

class FPGA:

    # def __init__(self, bit_file_path):
    #     self.ol = Overlay(bit_file_path)
    #     self.dma = self.ol.axi_dma_0
    

    def get_mock_output(self, processed_input, mapping):
      
        if len(input) < 20:
            print("function submit_input: input length is less than 20")
            return []
        processed_input = Parser.flatten_list()

        random_classification = random.randint(0, 5)
        return mapping[random_classification]

    # def get_output(self, input):
    #     start_time = time.time()

    #     for element in range(len(in_buffer)):
    #         in_buffer[element] = unpack('i', pack('i', second_buffer[element]))[0]

    #     out_buffer = allocate(shape=(4,), dtype=np.int32)
    #     self.dma.sendchannel.transfer(in_buffer)
    #     self.dma.recvchannel.transfer(out_buffer)
    #     self.dma.sendchannel.wait()
    #     self.dma.recvchannel.wait()
    #     out = (out_buffer[0:3])
    #     out = out_buffer.tolist()
    #     print("output: ", out)
    #     print("--- %s seconds ---" % (time.time() - start_time))

