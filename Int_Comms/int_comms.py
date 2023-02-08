'''
Links referenced:
https://ianharvey.github.io/bluepy-doc/
https://www.geeksforgeeks.org/python-output-formatting/
'''
import sys
import time
from threading import Thread
import crc8
from bluepy import btle
from bluepy.btle import BTLEException, Peripheral
from datetime import datetime
from math import floor

connection_threads = {}
'''
"B0:B1:13:2D:D4:AB"
"B0:B1:13:2D:CD:A2" 
"B0:B1:13:2D:D4:89"
"B0:B1:13:2D:B3:08"
"B0:B1:13:2D:D8:AC"
"B0:B1:13:2D:D8:8C"
'''
beetle_addresses = ["B0:B1:13:2D:D4:AB", "B0:B1:13:2D:D4:89", "B0:B1:13:2D:D8:AC"]
beetle_status = {}
PACKET_LENGTH = 20

# https://careerkarma.com/blog/python-string-to-int/
class MyDelegate(btle.DefaultDelegate):
    def __init__(self, connection_index):
        btle.DefaultDelegate.__init__(self)
        self.connection_index = connection_index
        self.ID = str(connection_index)
        self.buffer = ""

    def handleNotification(self, cHandle, data):
        print(connection_threads[self.connection_index].addr, " ", data)
        print("\r                                                       \r")
        self.buffer += clean_data(str(data))
        
        connection_threads[self.connection_index].total_data_received += utf8len(str(data))
        connection_threads[self.connection_index].data_rate()
        
        if(len(self.buffer) >= 20):
            data_string = self.buffer[:PACKET_LENGTH]
            #print("data_string used: ", data_string)
            self.buffer = self.buffer[PACKET_LENGTH:]
            if crc_check(data_string):
                BEETLE_ID = data_string[0]
                PACKET_ID = data_string[1]
                DATA = clear_padding(data_string[2:-2])
                print("\rdata received from ", BEETLE_ID)
                print("\r                                                       \r")
                #(BEETLE_ID == self.ID) and 
                connection_threads[self.connection_index].last_sync_time = datetime.now()
                if ((PACKET_ID == '0') and (DATA == "ACK")):
                    print("\rACK received")
                    connection_threads[self.connection_index].ACK = True
                elif ((PACKET_ID == '1') and (DATA == "HANDSHAKE")):
                    print("\rHandshake reply received")
                    connection_threads[self.connection_index].handshake_status = True
                elif ((PACKET_ID == '2') and (DATA == "WAKEUP")):
                    print("\rWakeup reply received")
                    connection_threads[self.connection_index].ACK = True
                elif ((PACKET_ID == '3') and (DATA == "GUN")):
                    print("\rPlayer has fired a shot")
                elif ((PACKET_ID == '4') and (DATA == "VEST")):
                    print("\rPlayer has been hit")
                elif ((PACKET_ID == '5')):
                    print("\rMotion sensor data packet 1 obtained")
                    extracted_data = unpack_data(DATA)
                    #print(extracted_data[0], " ", extracted_data[1], " ", extracted_data[2])
                    connection_threads[self.connection_index].packet_0 = True
                    connection_threads[self.connection_index].current_data["roll"] = extracted_data[0]
                    connection_threads[self.connection_index].current_data["pitch"] = extracted_data[1]
                    connection_threads[self.connection_index].current_data["yaw"] = extracted_data[2]
                elif ((PACKET_ID == '6')):
                    print("Motion sensor data packet 2 obtained", end = "\r")
                    extracted_data = unpack_data(DATA)
                    #print(extracted_data[0], " ", extracted_data[1], " ", extracted_data[2])
                    connection_threads[self.connection_index].packet_1 = True
                    connection_threads[self.connection_index].current_data["accX"] = extracted_data[0]      
                    connection_threads[self.connection_index].current_data["accY"] = extracted_data[1]   
                    connection_threads[self.connection_index].current_data["accZ"] = extracted_data[2] 
                    
                print("\r                                                       \r")            
            else:
                print("\rERR in CRC")
                #reset all boolean when error in packet
                connection_threads[self.connection_index].error = True
                #connection_threads[self.connection_index].packet_0 = False
                #connection_threads[self.connection_index].packet_1 = False
                time.sleep(0.01)

# data processing for incoming packets


def clean_data(info):
    return (info[2:-1])

# remove padded '#' from message


def clear_padding(data):
    while True:
        if (data[0] == '#'):
            data = data[1:]
        else:
            return data

# obtain imu value from string
def unpack_data(data):
    signs   = int(data[0])
    value_1 = int(data[1:6]) / 100
    value_2 = int(data[6:11]) / 100
    value_3 = int(data[11:16]) / 100
    if (signs % 2 != 0):
        value_3 = -value_3
    if ((signs/2) % 2 != 0):
        value_2 = -value_2
    if ((floor(signs/2)/2) % 2 != 0):
        value_1 = -value_1
    return value_1, value_2, value_3

# return size of packet received https://stackoverflow.com/questions/30686701/python-get-size-of-string-in-bytes
def utf8len(s):
    return len(s.encode('utf-8'))

# CRC check https://pypi.org/project/crc8/

def crc_check(data_string):
    hash = crc8.crc8()
    crc = data_string[-2:]
    data_string = data_string[2:-2]
    hash.update(bytes(data_string, "utf-8"))
    if (hash.hexdigest() == crc):
        return True
    else:
        return False

# Thread generation for each beetle
# To use for timeout to trigger sending of wakeup call https://pynative.com/python-get-time-difference/
# https://www.w3schools.com/python/python_dictionaries.asp


class BeetleThread(Thread):
    start_time = datetime.now()
    last_sync_time = start_time
    current_time = start_time
    handshake_status = False
    ACK = False
    err_count = 0
    packet_0 = False
    packet_1 = False
    total_data_received = 0
    error = False
    current_data = {
        "roll": "#",
        "pitch": "#",
        "yaw": "#",
        "accX": "#",
        "accY": "#",
        "accZ": "#",
    }

    def __init__(self, connection_index, addr, reconnect):
        Thread.__init__(self)
        self.connection_index = connection_index
        self.addr = addr
        self.reconnect = reconnect

    def run(self):
        self.establish_connection()
        time.sleep(12.0)
        try:
            # handshake at start of thread
            self.handshake(self.pheripheral)
            
            while True:
                self.current_time = datetime.now()
                time_diff = self.current_time - self.last_sync_time
                if (time_diff.total_seconds() > 60):
                    self.wakeup(self.pheripheral)
                    self.last_sync_time = datetime.now()

                # call data collecting comms
                self.receive_data(self.connection)

        except BTLEException:
            # enter when disconnected
            self.connection.disconnect()
            # start a function to create new thread after reconnecting
            reconnect = Thread(target=reconnection(
                self.addr, self.connection_index))
            reconnect.start()
            # end current thread as new one will be started after reconnection
            sys.exit(1)

    def handshake(self, p):
        while (not self.handshake_status):
            count = 0
            # Send handshake packet
            self.send_data("H")
            print("\rHANDSHAKE SENT")
            # Wait for Handshake packet from bluno
            while(count < 5):
                #print(self.connection_index, " waiting for handshake...")
                p.waitForNotifications(4)
                time.sleep(0.1)
                count += 1
        # Send back 
        print("\rHANDSHAKE RECEIVED, RETURN ACK")
        self.send_data("A")
        time.sleep(10.0)

    def wakeup(self, p):
        # Send handshake pac
        print("\rWAKE UP CALL")
        self.send_data("W")
        # Wait for ack packet from bluno
        while (not self.ACK):
            p.waitForNotifications
        print("\rWAKEUP ACKED")
        self.ACK = False

    def receive_data(self, p):
        # some loops to ensure all packets are received
        for x in range(2):
            p.waitForNotifications(0.1)
        if self.error:
            if (self.err_count > 8):
                raise BTLEException("continous error in packet from ", self.connection_index)
            self.err_count = self.err_count+1
            self.error = False
        if self.packet_0 & self.packet_1:
            print("\rFull motion sensor data received")
            #print("\r", self.current_data)
            self.packet_0 = False
            self.packet_1 = False
            
    def data_rate(self):
        print("\rData rate:", self.total_data_received / (datetime.now() - self.start_time).total_seconds() )
        
    def send_data(self, message):
        #print(message, " message sent to ", self.connection_index)
        for characteristic in self.characteristic:
                characteristic.write(bytes(message, "UTF-8"), withResponse=False)
        
    def establish_connection(self):
        while True:
            try:
                print("connecting to ", self.addr)
                print("\r                                                       \r")
                self.pheripheral = Peripheral(self.addr)
                beetle_status[self.connection_index] = self.pheripheral
                self.service = self.pheripheral.getServices()
                self.characteristic = self.pheripheral.getCharacteristics()
                self.pheripheral.setDelegate(MyDelegate(self.connection_index))
                print("connecting to ", self.addr)
                print("\r                                                       \r")
                break
            except BTLEException:
                time.sleep(3)


def reconnection(addr, index):
    print("\rreconnecting bluno")
    while True:
        try:
            print("\rreconnecting to %s" % (addr))
            p = btle.Peripheral(addr)
            print("\rre-connected to %s" % (addr))
            beetle_status[index] = p
            t = BeetleThread(index, addr, True, p)
            # start thread
            t.start()
            connection_threads[index] = t
            break
        except Exception:
            time.sleep(1)
            continue


def main():
    for i in range(len(beetle_addresses)):
        t = BeetleThread(i, beetle_addresses[i], False)
        t.start()
        connection_threads[i] = t

if __name__ == "__main__":
    main()

        
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
Just keep sending from arduino periodically at ard every 200ms(??)
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