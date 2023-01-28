import bluepy
from bluepy import btle
from bluepy.btle import BTLEException, Scanner, BTLEDisconnectError, Peripheral
import threading
import concurrent
from concurrent import futures
import time

dev = Peripheral("B0:B4:48:BF:C9:83") 
dev.connect(dev.addr)
print("Rched here")