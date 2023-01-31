import bluepy
from bluepy import btle
from bluepy.btle import BTLEException, Scanner, BTLEDisconnectError, Peripheral
import threading
import concurrent
from concurrent import futures
import time


class MyDelegate(btle.DefaultDelegate):

    def __init__(self, params):
        btle.DefaultDelegate.__init__(self)

    def handleNotification(self,cHandle,data):
        global addr_var
        global delegate_global
        print('got data: ', data)

address = "B0:B1:13:2D:CD:A2"
dev = Peripheral(address) 
print("Rched here")
dev.setDelegate(MyDelegate(address))




characteristics = dev.getCharacteristics()
for characteristic in dev.getCharacteristics():
    characteristic.write(bytes('A', 'UTF-8'), withResponse=False)
    

while True:
    if dev.waitForNotifications(1.0):
        for characteristic in dev.getCharacteristics():
            characteristic.write(bytes('A', 'UTF-8'), withResponse=False)
        print("ack sent")
        continue