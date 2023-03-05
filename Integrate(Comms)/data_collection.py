import time
import crc8
from bluepy import btle
from bluepy.btle import BTLEException, Peripheral
from datetime import datetime
from math import floor

import csv

#variables for beetle
connection_threads = {}
'''
all beetle address
"B0:B1:13:2D:D4:AB" - motion sensor
"B0:B1:13:2D:B3:08" - motion sensor
'''
beetle_addresses = ["B0:B1:13:2D:D4:AB"]
#beetle_addresses = ["B0:B1:13:2D:B3:08"]
beetle_status = {}
PACKET_LENGTH = 20

#constants for print formatting
CR = "\r"
SPACE = "            "
END = ""


# https://careerkarma.com/blog/python-string-to-int/
class MyDelegate(btle.DefaultDelegate):
    def __init__(self, connection_index):
        btle.DefaultDelegate.__init__(self)
        self.connection_index = connection_index
        self.ID = str(connection_index)
        self.buffer = ""

    def handleNotification(self, cHandle, data):
        
        self.buffer += clean_data(str(data))
        global packet_1
        global packet_0
        global handshake_reply
        
        if(len(self.buffer) >= PACKET_LENGTH):
            data_string = self.buffer[:PACKET_LENGTH]
            #print("data_string used: ", data_string)
            self.buffer = self.buffer[PACKET_LENGTH:]
            if crc_check(data_string):
                
                #process incoming packet
                PACKET_ID = data_string[1]
                DATA = clear_padding(data_string[2:-2])
                
                #handle packet from beetle
                if ((PACKET_ID == '1') and (DATA == "HANDSHAKE")):
                    print(CR, "Handshake reply received", SPACE, end = END)
                    handshake_reply = True
                elif ((PACKET_ID == '5')):
                    #print(CR, "Motion sensor data packet 1 obtained", SPACE, end = END)
                    extracted_data = unpack_data(DATA)
                    packet_0 = True
                    current_data["roll"] = extracted_data[0]
                    current_data["pitch"] = extracted_data[1]
                    current_data["yaw"] = extracted_data[2]
                elif ((PACKET_ID == '6')):
                    extracted_data = unpack_data(DATA)
                    packet_1 = True
                    current_data["accX"] = extracted_data[0]      
                    current_data["accY"] = extracted_data[1]   
                    current_data["accZ"] = extracted_data[2] 
                    
                            
            else:
                print(CR, "ERR in CRC: ", data_string)
                self.buffer = ""
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

start_time = datetime.now()
last_sync_time = start_time
current_time = start_time
handshake_reply = False
handshake_completed = False
ACK = False
packet_0 = False
packet_1 = False
packet_0_rcv_time = start_time
packet_1_rcv_time = start_time
total_data_received = 0
error = False
err_count = 0
current_data = {
    "id"    : "#",
    "roll"  : "#",
    "pitch" : "#",
    "yaw"   : "#",
    "accX"  : "#",
    "accY"  : "#",
    "accZ"  : "#",
}

def handshake(p, characteristic):
    while (not handshake_reply):
        count = 0
        # Send handshake packet
        send_data("H", characteristic)
        print("HANDSHAKE SENT")
        # Wait for Handshake packet from bluno, sent handshake req agn if not received after some time
        while(count < 5):
            #print(self.connection_index, " waiting for handshake...")
            p.waitForNotifications(1)
            time.sleep(0.1)
            count += 1
            if(handshake_reply):
                break
    # Send back 
    print("HANDSHAKE RECEIVED, RETURN ACK")
    send_data("A", characteristic)
    count = 0
    time.sleep(2.0)
    print("HANDSHAKE COMPLETED")
    
def send_data(message, characteristics):
    for characteristic in characteristics:
            characteristic.write(bytes(message, "UTF-8"), withResponse=False)

fieldnames = [
    "roll" ,
    "pitch",
    "yaw"  ,
    "accX" ,
    "accY" ,
    "accZ" 
]

current_data = {
    "roll"  : "#",
    "pitch" : "#",
    "yaw"   : "#",
    "accX"  : "#",
    "accY"  : "#",
    "accZ"  : "#",
}

empty_data = {
    "roll"  : "",
    "pitch" : "",
    "yaw"   : "",
    "accX"  : "",
    "accY"  : "",
    "accZ"  : "",
}


def main():
    global packet_0
    global packet_1
    
    while True:
        try:
            print("CONNECTING TO")
            pheripheral = Peripheral(beetle_addresses[0])
            characteristic = pheripheral.getCharacteristics()
            pheripheral.setDelegate(MyDelegate(0))
            print("CONNECTED TO ", beetle_addresses[0])
            break
        except BTLEException:
            time.sleep(3)
    handshake(pheripheral, characteristic)
    packet_received = 0
    
    print("Collecting data")
    with open('./expected_data.csv', 'w', encoding='UTF8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
    
        while True:
            input()
            start_time = datetime.now()
            send_data("R", characteristic)
            print("START COLLECTING")
            while True:
                pheripheral.waitForNotifications(0.1)
                    
                if packet_0 and packet_1:
                    packet_received += 1
                    writer.writerow(current_data)
                    packet_0 = False
                    packet_1 = False
                
                if( (datetime.now() - start_time).total_seconds()) > 1.3:
                    print("END COLLECTION")
                    print(packet_received)
                    packet_received = 0
                    break
                    
            writer.writerow(empty_data)

if __name__ == "__main__":
    main()