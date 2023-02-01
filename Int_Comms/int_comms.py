'''
Links referenced:
https://ianharvey.github.io/bluepy-doc/
https://www.geeksforgeeks.org/python-output-formatting/
'''

import bluepy
from bluepy import btle
from bluepy.btle import BTLEException, Scanner, BTLEDisconnectError, Peripheral
import threading
import concurrent
from concurrent import futures
import time
import struct
import crc8
import asyncio

#manually input all address here
address = "B0:B1:13:2D:CD:A2"
beetle_addresses = ["B0:B1:13:2D:CD:A2"]
beetle_status = [0]
global beetle_handshake 
beetle_handshake = [False]

class MyDelegate(btle.DefaultDelegate):

    def __init__(self, params):
        btle.DefaultDelegate.__init__(self)

    #this is asynchronous
    def handleNotification(self,cHandle,data):
        global addr_var
        global delegate_global
        #print("got data: ")
        unpacked = struct.unpack('c c h h h h h h h h h', data)
        #print("From: %1d \nSeq num: %1d\nType: %c" % (unpacked[2]/10, unpacked[2]%10, unpacked[0]) )
        if unpacked[0] == 'V':
            acknowledge(self)
        elif unpacked[0] == 'A':
            beetle_handshake[0] = True
            acknowledge(self)

def establish_connection():
    while True:
        try:
            for i in range(len(beetle_addresses)):
                # for initial connections or when any beetle is disconnected
                if beetle_addresses[i] == address:
                    if beetle_status[i] != 0:  # do not reconnect if already connected
                        return
                    else:
                        print("connecting with %s" % (address))
                        # Peripheral is used to connect, .connect is used for reconnecting
                        beetle = Peripheral(address) 
                        beetle.setDelegate(MyDelegate(address))
                        beetle_status[i] = beetle
                        print("Connected to %s" % (address))
                        handshake(beetle, 0)
                        return
        except Exception as e:
            print(e)
            for i in range(len(beetle_addresses)):
                # for initial connections or when any beetle is disconnected
                if beetle_addresses[i] == address:
                    if beetle_status[i] != 0:  # do not reconnect if already connected
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
        
def acknowledge(beetle):
    for characteristic in beetle.getCharacteristics():
        characteristic.write(bytes('A', 'UTF-8'), withResponse=False)
    print("ack sent")

def handshake(beetle, id):
    for characteristic in beetle.getCharacteristics():
        characteristic.write(bytes('H', 'UTF-8'), withResponse=False)
    print("handshake sent")
    beetle.waitForNotifications(2)
    if(beetle_handshake[id] == False):
        handshake(beetle, id)

#Fucntion to check CRC match data receive
def crc_check(data_string):
    hash = crc8.crc8()
    crc = data_string[-2:]
    data_string = data_string[2:-2]
    hash.update(bytes(data_string, "utf-8"))
    if (hash.hexdigest() == crc):
        return True
    else:
        return False
    
if __name__ == '__main__':
    establish_connection()
    '''
    while True:
        for i in range(len(beetle_addresses)):
            for characteristic in i.getCharacteristics():
                characteristic.write(bytes('A', 'UTF-8'), withResponse=False)
        asyncio.sleep(1)
    '''
        
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
sent wakeup call every 5s to gun and vest
timer for motion: reconnect if no data receive for a period of time

'''