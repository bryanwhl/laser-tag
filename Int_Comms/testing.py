import bluepy
from bluepy import btle
from bluepy.btle import BTLEException, Scanner, BTLEDisconnectError, Peripheral
import threading
import concurrent
from concurrent import futures
import time

#manually input all address here
address = "B0:B1:13:2D:CD:A2"
beetle_addresses = ["B0:B1:13:2D:CD:A2"]
beetle_status = [0]
beetle_handshake = [False]

class MyDelegate(btle.DefaultDelegate):

    def __init__(self, params):
        btle.DefaultDelegate.__init__(self)

    def handleNotification(self,cHandle,data):
        global addr_var
        global delegate_global
        print('got data: ', data)


'''
dev = Peripheral(address) 
dev.setDelegate(MyDelegate(address))
'''


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
                        handshake(beetle)
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

def handshake(beetle):
    for characteristic in beetle.getCharacteristics():
        characteristic.write(bytes('A', 'UTF-8'), withResponse=False)
    

while True:
    if dev.waitForNotifications(1.0):
        for characteristic in dev.getCharacteristics():
            characteristic.write(bytes('A', 'UTF-8'), withResponse=False)
        print("ack sent")
        continue
    
if __name__ == '__main__':
    establish_connection()