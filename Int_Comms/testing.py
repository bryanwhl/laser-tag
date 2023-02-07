import sys
import time
from threading import Thread
import crc8
from bluepy import btle
from bluepy.btle import BTLEException, Peripheral
from datetime import datetime

service_uuid = "0000dfb0-0000-1000-8000-00805f9b34fb"

connection_threads = {}
address = "B0:B1:13:2D:CD:A2"
beetle_addresses = ["B0:B1:13:2D:CD:A2"]
beetle_status = {}

# https://careerkarma.com/blog/python-string-to-int/
class MyDelegate(btle.DefaultDelegate):
    def __init__(self, connection_index):
        btle.DefaultDelegate.__init__(self)
        self.connection_index = connection_index
        self.ID = str(connection_index)

    def handleNotification(self, cHandle, data):
        print(data)
        data_string = clean_data(str(data))
        if crc_check(data_string):
            BEETLE_ID = data_string[0]
            PACKET_ID = data_string[1]
            DATA = clear_padding(data_string[2:-2])
            print("data received from ", BEETLE_ID)
            connection_threads[self.connection_index].last_sync_time = datetime.now()
            connection_threads[self.connection_index].total_data_received += utf8len(data)
            connection_threads[self.connection_index].data_rate()
            if ((BEETLE_ID == self.ID) and (PACKET_ID == '0') and (DATA == "ACK")):
                print("ACK received")
                connection_threads[self.connection_index].ACK = True
            if ((BEETLE_ID == self.ID) and (PACKET_ID == '1') and (DATA == "HANDSHAKE")):
                print("Handshake reply received")
                connection_threads[self.connection_index].handshake_status = True
            if ((BEETLE_ID == self.ID) and (PACKET_ID == '2') and (DATA == "WAKEUP")):
                print("Wakeup reply received")
                connection_threads[self.connection_index].ACK = True
            if ((BEETLE_ID == self.ID) and (PACKET_ID == '3') and (DATA == "GUN")):
                print("Player has fired a shot")
            if ((BEETLE_ID == self.ID) and (PACKET_ID == '4') and (DATA == "VEST")):
                print("Player has been hit")
            if ((BEETLE_ID == self.ID) and (PACKET_ID == '5')):
                print("Motion sensor data packet 1 obtained")
                extracted_data = unpack_data(DATA)
                print(extracted_data[0], " ", extracted_data[1], " ", extracted_data[2])
                connection_threads[self.connection_index].packet_0 = True
                connection_threads[self.connection_index].current_data["roll"] = extracted_data[0]
                connection_threads[self.connection_index].current_data["pitch"] = extracted_data[1]
                connection_threads[self.connection_index].current_data["yaw"] = extracted_data[2]
            if ((BEETLE_ID == self.ID) and (PACKET_ID == '6')):
                print("Motion sensor data packet 2 obtained")
                extracted_data = unpack_data(DATA)
                print(extracted_data[0], " ", extracted_data[1], " ", extracted_data[2])
                connection_threads[self.connection_index].packet_1 = True
                connection_threads[self.connection_index].current_data["accX"] = extracted_data[0]      
                connection_threads[self.connection_index].current_data["accY"] = extracted_data[1]   
                connection_threads[self.connection_index].current_data["accZ"] = extracted_data[2]             
        else:
            print("ERR in CRC")
            #reset all boolean when error in packet
            connection_threads[self.connection_index].error = True
            connection_threads[self.connection_index].packet_0 = False
            connection_threads[self.connection_index].packet_1 = False
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
    if (signs % 2 == 1):
        value_3 = -value_3
    if ((signs/2) % 2 == 1):
        value_2 = -value_2
    if ((signs/4) % 2 == 1):
        value_1 = -value_1
    return value_1, value_2, value_3

# return size of packet received
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
    current_data = {
        "roll": "#",
        "pitch": "#",
        "yaw": "#",
        "accX": "#",
        "accY": "#",
        "accZ": "#",
    }

    def __init__(self, connection_index, addr, reconnect):
        print("connected to", addr, "\n")
        Thread.__init__(self)
        self.connection_index = connection_index
        self.addr = addr
        self.connection = (beetle_status[self.connection_index])
        self.connection.setDelegate(MyDelegate(self.connection_index))
        self.reconnect = reconnect
        self.service = self.connection.getServiceByUUID(service_uuid)
        self.characteristic = self.service.getCharacteristics()[0]

    def run(self):
        try:
            # handshake at start of thread
            self.handshake(self.connection)

            while True:
                self.current_time = datetime.now()
                time_diff = self.current_time - self.last_sync_time
                if (time_diff.total_seconds() > 60):
                    self.wakeup(self.connection)
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
        # Send handshake packet
        self.characteristic.write(bytes("H", "utf-8"), withResponse=False)
        print("HANDSHAKE SENT")
        # Wait for Handshake packet from bluno
        while (not self.handshake_status):
            p.waitForNotifications(2)
            time.sleep(0.1)
        # Send back ACK
        print("HANDSHAKE RECIEVED, RETURN ACK")
        while (not self.ACK):
            time.sleep(0.5)
            self.characteristic.write(bytes("A", "utf-8"), withResponse=False)
            p.waitForNotifications(2)
        self.ACK = False

    def wakeup(self, p):
        # Send handshake packet
        print("WAKE UP CALL")
        self.characteristic.write(bytes("W", "utf-8"), withResponse=False)
        # Wait for ack packet from bluno
        while (not self.ACK):
            p.waitForNotifications(2)
        self.ACK = False

    def receive_data(self, p):
        # some loops to ensure all packets are received
        for x in range(4):
            p.waitForNotifications(0.1)
        if error:
            if (self.err_count > 8):
                raise BTLEException("continous error in packet from ", self.connection_index)
            self.err_count = self.err_count+1
            error = False
        if self.packet_0 & self.packet_1:
            print("Full motion sensor data received")
            print(self.current_data)
            
    def data_rate(self):
        print("Data rate:", self.total_data_received / (datetime.now() - self.start_time()).total_seconds() )
        


def establish_connection():
    print("Connecting to bluno ...")
    while True:
        try:
            for i in range(len(beetle_addresses)):
                p = Peripheral(beetle_addresses[i])
                beetle_status[i] = p
                # print(beetle_status[i])
                t = BeetleThread(i, beetle_addresses[i], False)
                # start thread
                t.start()
                connection_threads[i] = t
        except BTLEException:
            for i in range(len(beetle_addresses)):
                if len(beetle_status) == 0:
                    return
                if beetle_status[i] != 0:  # do not reconnect if already connected
                    return
            time.sleep(3)


def reconnection(addr, index):
    print("reconnecting bluno")
    while True:
        try:
            print("reconnecting to %s" % (addr))
            p = btle.Peripheral(addr)
            print("re-connected to %s" % (addr))
            beetle_status[index] = p
            t = BeetleThread(index, addr, True)
            # start thread
            t.start()
            connection_threads[index] = t
            break
        except Exception:
            time.sleep(1)
            continue


def main():
    establish_connection()


if __name__ == "__main__":
    main()
