'''
Links referenced:
https://ianharvey.github.io/bluepy-doc/
'''

import bluepy
from bluepy import btle
from bluepy.btle import BTLEException, Scanner, BTLEDisconnectError, Peripheral
import threading
import concurrent
from concurrent import futures
import time

dev = btle.Peripheral("B0:B4:48:BF:C9:83") 

beetle_addresses = ["50:F1:4A:CC:01:C4", 
                    "50:F1:4A:CB:FE:EE", 
                    "78:DB:2F:BF:2C:E2",
                    "1C:BA:8C:1D:30:22"]

class MyDelegate(btle.DefaultDelegate):

    def __init__(self,params):
        btle.DefaultDelegate.__init__(self)

    def handleNotification(self,cHandle,data):
        global addr_var
        global delegate_global
        print('got data: ', data)
        try:
            data_decoded = struct.unpack("b",data)
            print("Address: "+addr_var[ii])
            print(data_decoded)
            return
        except:
            pass

def establish_connection(address):
    while True:
        try:
            for idx in range(len(beetle_addresses)):
                # for initial connections or when any beetle is disconnected
                if beetle_addresses[idx] == address:
                    if global_beetle[idx] != 0:  # do not reconnect if already connected
                        return
                    else:
                        print("connecting with %s" % (address))
                        # Peripheral is used to connect, .connect is used for reconnecting
                        beetle = Peripheral(address) 
                        global_beetle[idx] = beetle
                        """"
                        beetle_delegate = Delegate(address)
                        global_delegate_obj[idx] = beetle_delegate
                        beetle.withDelegate(beetle_delegate)
                        if address != "50:F1:4A:CC:01:C4":
                            initHandshake(beetle)
                        """
                        print("Connected to %s" % (address))
                        return
        except Exception as e:
            print(e)
            for idx in range(len(beetle_addresses)):
                # for initial connections or when any beetle is disconnected
                if beetle_addresses[idx] == address:
                    if global_beetle[idx] != 0:  # do not reconnect if already connected
                        return
            time.sleep(3)


def reconnect(beetle):
    while True:
        try:
            print("reconnecting to %s" % (beetle.addr))
            beetle.connect(beetle.addr)
            print("re-connected to %s" % (beetle.addr))
            return
        except:
            time.sleep(1)
            continue
        
        
if __name__ == '__main__':
    global_beetle = []
    [global_beetle.append(0) for idx in range(len(beetle_addresses))]
    #for beetle in global_beetle:
        #initHandshake(beetle)
        
        
        
        
        
        
        
'''
Protocols:
handshake at start for all 6

gun & vest:
stop & wait for now
use timer to send wakeup call?
arduino side to retransmit after 100ms(??) of waiting for ack (ack or packet is lost)
packet will have sequence number alternating between 1 and 0 (prevent duplicate packet if ack is lost)
laptop send ack if packet received is correct, nack if packet is corrupted

motion sensor:
UDP (standardised data rate)
Just keep sending from arduino periodically
PC will drop corrupted packet 
No action if packet lost

Points to note:
use CRC
packet fragmentation for large packet(only applicable for sensor)
20byte for all packet. pad small packet and fragment big packet
no timer for disconnection

'''