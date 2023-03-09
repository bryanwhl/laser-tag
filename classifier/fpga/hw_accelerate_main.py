import time

from fpga import FPGA

BASE_DIR = '/home/xilinx/'

BITFILE_PATH = BASE_DIR + "classify.bit"

def fpga_setup(bitfile_path):
    start = time.time()
    fpga = FPGA(bitfile_path)
    print("Bitfile Loading Time: " + str(time.time() - start) + "s")
    return fpga

if __name__ == "__main__":
    fpga = fpga_setup(BITFILE_PATH)
