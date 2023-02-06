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
                connection_threads[self.connection_index].packet_0 = True
            if ((BEETLE_ID == self.ID) and (PACKET_ID == '6')):
                connection_threads[self.connection_index].packet_1 = True
                print("Motion sensor data packet 2 obtained")
        else:
            print("ERR in CRC")
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


class BeetleThread(Thread):
    last_sync_time = datetime.now()
    current_time = datetime.now()
    handshake_status = False
    ACK = False
    clear = False
    sync = False
    millis = 0
    err_count = 0
    timer_count = 0
    packet_0 = False
    packet_1 = False
    current_data = {
        "roll": "#",
        "pitch": "#",
        "yaw": "#",
        "AccX": "#",
        "AccY": "#",
        "AccZ": "#",
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
        self.handshake = False
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
        self.timer_count = 0

    def receive_data(self, p):
        error = False
        # recieve info for current data set
        while True:
            self.current_data = {
                "roll": "#",
                "pitch": "#",
                "yaw": "#",
                "AccX": "#",
                "AccY": "#",
                "AccZ": "#",
            }
            # some loops to ensure all packets supposed to be recieved
            for x in range(6):
                p.waitForNotifications(0.1)
                # print(self.current_data)
                if (self.current_data["millis"] != '#'):
                    break
            if error:
                if (self.err_count > 8):
                    raise BTLEException("error")
                self.err_count = self.err_count+1
                error = False
                continue
            self.err_count = 0


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
                # for initial connections or when any beetle is disconnected
                if beetle_addresses[i] == address:
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
