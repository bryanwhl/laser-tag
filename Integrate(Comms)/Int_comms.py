import sys
import time
import socket
from Process_packet import *
from socket import *
from threading import Thread
from threading import Event
from bluepy import btle
from bluepy.btle import BTLEException, Peripheral
from datetime import datetime
from math import floor
from queue import Queue
from signal import signal, SIGPIPE, SIG_DFL
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from base64 import b64encode, b64decode

signal(SIGPIPE, SIG_DFL)

exit_signal = Event()

# Init connection settings
HOST = "localhost"
PORT = 8888

# Init Encryption settings
key = "thisismysecretky"
key = bytes(str(key), encoding="utf8")

# variables for beetle
connection_threads = {}
'''
all beetle address
"B0:B1:13:2D:D4:AB" - motion sensor
"B0:B1:13:2D:CD:A2" - gun
"B0:B1:13:2D:D4:89" - vest
"B0:B1:13:2D:B3:08" - motion sensor
"B0:B1:13:2D:D8:AC" - vest
"B0:B1:13:2D:D8:8C" - gun
'''
beetle_addresses = [
    "B0:B1:13:2D:D4:AB",
    "B0:B1:13:2D:CD:A2",
    "B0:B1:13:2D:D4:89",
    "B0:B1:13:2D:B3:08",
    "B0:B1:13:2D:D8:AC",
    "B0:B1:13:2D:D8:8C",

]
beetle_status = {}
PACKET_LENGTH = 20

# constants for print formatting
CR = "\r"
SPACE = "            "
END = ""

# queue to send to server
motion_msg = Queue(maxsize=1269)
vest_msg = Queue(maxsize=1269)
gun_msg = Queue(maxsize=1269)

# queue to receive from server
hp_one = []
hp_two = []
bullet_one = []
bullet_two = []

# for updating beetle status
alphabets = "abcdefghijklmnopqrstuvwxyz"


class ExternalComms(Thread):

    def __init__(self):
        Thread.__init__(self)

    def receive_from_ultra(self, conn_socket):
        while True:
            # Receive and Parse message (len_EncryptedMessage)
            # recv length followed by '_' followed by cypher
            message = b''
            while not message.endswith(b'_'):
                _d = conn_socket.recv(1)
                if not _d:
                    message = b''
                    break
                message += _d
            if len(message) == 0:
                print('no more data from the client')
                conn_socket.close()
                return

            message = message.decode("utf-8")
            length = int(message[:-1])
            message = b''
            while len(message) < length:
                _d = conn_socket.recv(length - len(message))
                if not _d:
                    message = b''
                    break
                message += _d
            if len(message) == 0:
                print('no more data from the client')
                conn_socket.close()
                return
            decodedMessage = b64decode(message)

            iv = decodedMessage[:AES.block_size]
            cipher = AES.new(key, AES.MODE_CBC, iv)
            decryptedMessage = cipher.decrypt(decodedMessage[16:])
            decryptedMessage = unpad(decryptedMessage, AES.block_size)
            decryptedMessage = decryptedMessage.decode()

            # Return list of hp and bullets
            hp_and_bullets = eval(decryptedMessage)
            hp_one.append(hp_and_bullets[0])
            hp_two.append(hp_and_bullets[1])
            bullet_one.append(hp_and_bullets[2])
            bullet_two.append(hp_and_bullets[3])

            print("HP1: ", hp_one)
            print("HP2: ", hp_two)
            print("Bullet1: ", bullet_one)
            print("Bullet2: ", bullet_two)

    def run(self):
        global vest_msg
        global gun_msg
        global motion_msg
        while True:
            try:
                print("connecting to server...")
                self.clientSocket = socket(AF_INET, SOCK_STREAM)
                # Create client socket and connect to server
                self.clientSocket = socket(AF_INET, SOCK_STREAM)
                self.clientSocket.connect((HOST, PORT))

                # Create thread to receive from Ultra96
                receiver_thread = Thread(
                    target=self.receive_from_ultra, args=(self.clientSocket,))
                receiver_thread.start()
                break
            except BrokenPipeError:
                time.sleep(0.1)

        print("connected to server...")
        try:
            while True:
                if not vest_msg.empty():
                    message = "vest " + str(vest_msg.get())
                    encodedMessage = message.encode()
                    # Encrypt data
                    cipher = AES.new(key, AES.MODE_CBC)
                    encryptedMessage = cipher.iv + \
                        cipher.encrypt(pad(encodedMessage, AES.block_size))
                    encryptedMessage_64 = b64encode(encryptedMessage)
                    len_byte = str(len(encryptedMessage_64)
                                   ).encode("utf-8") + b'_'
                    finalmsg = len_byte+encryptedMessage_64
                    self.clientSocket.send(finalmsg)
                    time.sleep(0.05)

                if not gun_msg.empty():
                    message = "gun " + str(gun_msg.get())
                    encodedMessage = message.encode()
                    # Encrypt data
                    cipher = AES.new(key, AES.MODE_CBC)
                    encryptedMessage = cipher.iv + \
                        cipher.encrypt(pad(encodedMessage, AES.block_size))
                    encryptedMessage_64 = b64encode(encryptedMessage)
                    len_byte = str(len(encryptedMessage_64)
                                   ).encode("utf-8") + b'_'
                    finalmsg = len_byte+encryptedMessage_64
                    self.clientSocket.send(finalmsg)
                    time.sleep(0.05)

                if not motion_msg.empty():
                    message = str(motion_msg.get())
                    encodedMessage = message.encode()
                    # Encrypt data
                    cipher = AES.new(key, AES.MODE_CBC)
                    encryptedMessage = cipher.iv + \
                        cipher.encrypt(pad(encodedMessage, AES.block_size))
                    encryptedMessage_64 = b64encode(encryptedMessage)
                    len_byte = str(len(encryptedMessage_64)
                                   ).encode("utf-8") + b'_'
                    finalmsg = len_byte+encryptedMessage_64
                    self.clientSocket.send(finalmsg)
                    print("sent")
                    time.sleep(0.05)
        except KeyboardInterrupt:
            print("Closing Client Socket")
            self.clientSocket.close()
            sys.exit(1)


class MyDelegate(btle.DefaultDelegate):
    def __init__(self, connection_index):
        btle.DefaultDelegate.__init__(self)
        self.connection_index = connection_index
        self.id = str(floor(connection_index/3))
        self.buffer = ""
        self.current_data = {
            "roll": -9999.0,
            "pitch": -9999.0,
            "yaw": -9999.0,
            "accX": -9999.0,
            "accY": -9999.0,
            "accZ": -9999.0
        }

    def handleNotification(self, cHandle, data):

        # add received data to buffer
        self.buffer += clean_data(str(data))

        # queue for external comms
        global vest_msg
        global gun_msg
        global motion_msg

        if (len(self.buffer) >= PACKET_LENGTH):
            data_string = self.buffer[:PACKET_LENGTH]
            # print("data_string used: ", data_string)
            self.buffer = self.buffer[PACKET_LENGTH:]
            if crc_check(data_string):
                # process incoming packet
                BEETLE_ID = data_string[0]
                PACKET_ID = data_string[1]
                received_data = clear_padding(data_string[2:-2])
                print(CR, "data from ", BEETLE_ID, end=END)

                # update last sync time that is used for wakeup/timeout calls
                connection_threads[self.connection_index].last_sync_time = datetime.now()

                # handle packet from beetle
                if ((PACKET_ID == '0') and (received_data == "ACK")):
                    # print(CR, "ACK received", SPACE, end = END)
                    connection_threads[self.connection_index].ACK = True
                elif ((PACKET_ID == '1') and (received_data == "HANDSHAKE")):
                    print(CR, "Handshake reply received", SPACE, end=END)
                    connection_threads[self.connection_index].handshake_reply = True
                elif ((PACKET_ID == '2') and (received_data == "WAKEUP")):
                    # print(CR, "Wakeup reply received", SPACE, end = END)
                    connection_threads[self.connection_index].ACK = True
                elif ((PACKET_ID == '3') and (received_data[1:] == "GUN")):
                    connection_threads[self.connection_index].send_ack = True
                    connection_threads[self.connection_index].rcv_seq_num = received_data[0]
                    if (received_data[0] == str(connection_threads[self.connection_index].seq_num)):
                        connection_threads[self.connection_index].correct_seq_num = True
                        gun_msg.put(floor(self.connection_index/3))
                        print(CR, "Player has fired a shot", SPACE)
                    else:  # when relay received packet but ack from relay is lost
                        connection_threads[self.connection_index].correct_seq_num = False
                elif ((PACKET_ID == '4') and (received_data[1:] == "VEST")):
                    connection_threads[self.connection_index].send_ack = True
                    connection_threads[self.connection_index].rcv_seq_num = received_data[0]
                    if (received_data[0] == str(connection_threads[self.connection_index].seq_num)):
                        connection_threads[self.connection_index].correct_seq_num = True
                        vest_msg.put(floor(self.connection_index/3))
                        print(CR, "Player has been hit", SPACE)
                    else:
                        connection_threads[self.connection_index].correct_seq_num = False
                elif ((PACKET_ID == '5')):
                    # print(CR, "Motion sensor data obtained", SPACE, end = END)
                    extracted_data = unpack_data(received_data)
                    # print(CR, extracted_data, SPACE, end=END)
                    # print(extracted_data[0], " ", extracted_data[1], " ", extracted_data[2])
                    if (connection_threads[self.connection_index].handshake_completed):
                        self.current_data["roll"] = float(extracted_data[0])
                        self.current_data["pitch"] = float(extracted_data[1])
                        self.current_data["yaw"] = float(extracted_data[2])
                        self.current_data["accX"] = float(extracted_data[3])
                        self.current_data["accY"] = float(extracted_data[4])
                        self.current_data["accZ"] = float(extracted_data[5])
                        message = "" + str(self.id) + " ["
                        message += str(self.current_data["roll"]) + ","
                        message += str(self.current_data["pitch"]) + ","
                        message += str(self.current_data["yaw"]) + ","
                        message += str(self.current_data["accX"]) + ","
                        message += str(self.current_data["accY"]) + ","
                        message += str(self.current_data["accZ"]) + "]"
                        motion_msg.put(message)
            else:
                print(CR, "ERR in CRC", SPACE, end=END)
                self.buffer = ""
                connection_threads[self.connection_index].error = True
                time.sleep(0.01)


class BeetleThread(Thread):
    start_time = datetime.now()
    is_motion_sensor = False
    last_sync_time = start_time
    current_time = start_time
    handshake_reply = False
    handshake_completed = False
    ACK = False
    error = False
    seq_num = 0
    send_ack = False
    correct_seq_num = False
    rcv_seq_num = "x"
    err_count = 0

    def __init__(self, connection_index, addr):
        Thread.__init__(self)
        self.connection_index = connection_index
        self.addr = addr
        if (addr == "B0:B1:13:2D:D4:AB" or addr == "B0:B1:13:2D:B3:08"):
            self.is_motion_sensor = True

    def run(self):
        self.establish_connection()
        time.sleep(1.0)
        try:
            # handshake at start of thread
            self.handshake(self.pheripheral)

            while not exit_signal.is_set():
                self.current_time = datetime.now()
                time_diff = self.current_time - self.last_sync_time
                if (time_diff.total_seconds() > 60):
                    self.wakeup(self.pheripheral)

                # call data collecting comms
                self.receive_data(self.pheripheral)

                if not self.is_motion_sensor:
                    self.update_beetles(self.pheripheral)

            raise KeyboardInterrupt()

        except BTLEException:
            self.pheripheral.disconnect()
            # start a function to create new thread after reconnecting
            reconnect = Thread(target=reconnection(
                self.addr, self.connection_index))
            reconnect.start()
            # end current thread to reset everything as new one will be started after reconnection
            sys.exit(1)

        except KeyboardInterrupt:
            print("Disconnecting from beetles: ", self.addr)
            self.pheripheral.disconnect()
            sys.exit(1)

    def handshake(self, p):
        while (not self.handshake_reply):
            count = 0

            # Send handshake packet
            self.send_data("H")
            print("HANDSHAKE SENT FOR ", self.addr)

            # Wait for Handshake reply packet from bluno, sent handshake req agn if not received after some time
            while (count < 5):
                p.waitForNotifications(1)
                time.sleep(0.1)
                count += 1
                if (self.handshake_reply):
                    break

        # Send back last ack to signal end of handshaking
        print("HANDSHAKE RECEIVED, RETURN ACK FOR", self.addr)
        self.send_data("A")
        self.handshake_reply = False
        count = 0

        # Wait 1 second in case there is retransmission of handshake by beetle
        while (count < 5):
            p.waitForNotifications(0.2)
            if (self.handshake_reply):
                count = 0
                self.send_data("A")
                self.handshake_reply = False
            count += 1
        self.handshake_completed = True

        # Wait for a while before starting operations
        time.sleep(1)
        self.start_time = datetime.now()

    def wakeup(self, p):
        count = 0
        print(CR, "WAKE UP CALL TO", self.addr, SPACE, end=END)
        # Wait for ack packet from bluno
        while (not self.ACK):
            self.send_data("W")
            p.waitForNotifications(0.5)
            count += 1
            if (count >= 7):
                raise BTLEException("BEETLE NOT WAKING UP ZZZ")
        print(CR, "WAKEUP ACKED FROM", self.addr, SPACE, end=END)
        self.ACK = False

    def receive_data(self, p):
        # some loops to ensure all packets are received
        for x in range(2):
            p.waitForNotifications(0.1)

        # for stop and wait
        if (self.send_ack):
            self.acknowledge_data()
            self.send_ack = False

        # if there is error in crc
        if self.error:
            if (self.err_count > 10):
                raise BTLEException("CONTINUOUS FAIL CRC :(")
            self.err_count = self.err_count+1
            self.error = False

    def update_beetles(self, p):
        global hp_one
        global hp_two
        global bullet_one
        global bullet_two
        hasData = False
        value = 0

        if (self.addr == "B0:B1:13:2D:D8:8C" and bullet_one):   # gun 1
            hasData = True
            count = 0
            value = bullet_one[-1]
            bullet_one.clear()
            if value == 1:
                value = 2
        elif (self.addr == "B0:B1:13:2D:CD:A2" and bullet_two):  # gun 2
            hasData = True
            count = 0
            value = bullet_two[-1]
            bullet_two.clear()
            if value == 1:
                value = 2
        elif (self.addr == "B0:B1:13:2D:D4:89" and hp_one):  # vest 1
            hasData = True
            count = 0
            value = hp_one[-1] / 10
            hp_one.clear()
        elif (self.addr == "B0:B1:13:2D:D8:AC" and hp_two):  # vest 2
            hasData = True
            count = 0
            value = hp_two[-1] / 10
            hp_two.clear()

        if hasData:
            print(CR, "UPDATE STATUS of :", self.addr, " ",
                value, alphabets[value], SPACE, end=END)
            # Wait for ack packet from bluno
            while (not self.ACK):
                self.send_data(str(alphabets[int(value)]))
                p.waitForNotifications(0.5)
                count += 1
                if (count >= 5):
                    raise BTLEException("BEETLE NOT RESPONDING ZZZ")
            print(CR, "STATUS UPDATE ACKED", SPACE, end=END)
            self.ACK = False

    def acknowledge_data(self):  # for stop and wait reply
        print(CR, "DATA RECEIVED. ACK SENT", SPACE, end=END)
        self.send_data(self.rcv_seq_num)
        if (self.correct_seq_num and self.seq_num == 1):
            self.seq_num = 0
        elif (self.correct_seq_num and self.seq_num == 0):
            self.seq_num = 1

    def send_data(self, message):  # sending a single byte(char) to beetle
        for characteristic in self.characteristic:
            characteristic.write(bytes(message, "UTF-8"), withResponse=False)

    def establish_connection(self):
        while True:
            try:
                print("CONNECTING TO ", self.addr)

                # Initialise connection with beetles
                self.pheripheral = Peripheral(self.addr)
                beetle_status[self.connection_index] = self.pheripheral
                self.service = self.pheripheral.getServices()
                self.characteristic = self.pheripheral.getCharacteristics()
                self.pheripheral.setDelegate(MyDelegate(self.connection_index))

                print("CONNECTED TO ", self.addr)
                break
            except BTLEException:
                time.sleep(1.5)


def reconnection(addr, index):
    while True:
        try:
            print(CR, "RECONNECTING %s" % (addr), SPACE, end=END)
            t = BeetleThread(index, addr)
            # start thread
            t.start()
            connection_threads[index] = t
            break
        except Exception:
            time.sleep(1)
            continue


def main():
    try:
        for i in range(len(beetle_addresses)):
            t = BeetleThread(i, beetle_addresses[i])
            t.start()
            connection_threads[i] = t
        x = ExternalComms()
        x.start()

        for i in range(len(beetle_addresses)):
            connection_threads[i].join()
        x.join()

    except KeyboardInterrupt:
        print("Ending Program... \nBye Bye...")
        exit_signal.set()


if __name__ == "__main__":
    main()


# https://stackoverflow.com/questions/47847392/keyboard-interrupt-sockets-and-threads
# https://superfastpython.com/thread-event-object-in-python/
# https://code.visualstudio.com/docs/editor/refactoring
