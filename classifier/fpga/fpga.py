from pynq import Overlay
from pynq import allocate

class FPGA():
    def __init__(self, bit_file_path):
        self.ol = Overlay(bit_file_path)

    def run_fpga(self, input):
        # TODO Build and test the below script for FPGA to retrieve input and do a sample run

        # assert input.shape == self.ishape_normal
        # ibuf_folded = input.reshape(self.ishape_folded)

        # # pack the input buffer, reversing both SIMD dim and endianness
        # ibuf_packed = finnpy_to_packed_bytearray(
        #     ibuf_folded, self.idt, reverse_endian=True, reverse_inner=True
        # )
        # # copy the packed data into the PYNQ buffer
        # # TODO optimization: pack directly into the PYNQ buffer?
        # np.copyto(self.ibuf_packed_device, ibuf_packed)

        # # set up the DMA and wait until all transfers complete
        # self.dma.sendchannel.transfer(self.ibuf_packed_device)
        # self.dma.recvchannel.transfer(self.obuf_packed)
        # self.dma.sendchannel.wait()
        # self.dma.recvchannel.wait()

        # # unpack the packed output buffer from accelerator
        # obuf_folded = packed_bytearray_to_finnpy(
        #     self.obuf_packed, self.odt, self.oshape_folded, reverse_endian=True, reverse_inner=True
        # )

        # obuf_normal = obuf_folded.reshape(self.oshape_normal)
        # return obuf_normal
