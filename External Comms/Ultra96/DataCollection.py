from socket import *
from threading import Thread, Timer
from base64 import b64encode, b64decode
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import json
from pygments import highlight, lexers, formatters
import datetime
from time import sleep
import sys
import csv
from struct import unpack, pack


# Init connection settings
DATA_HOST = gethostname()
DATA_PORT = 8080

# Init Queues
gun_one_queue = []
gun_two_queue = []
vest_one_queue = []
vest_two_queue = []
motion_one_queue = []
motion_two_queue = []
action_one_queue = []
action_two_queue = []

message_queue = []

global action_flag_1
global action_flag_2
global last_action_time_1
global last_action_time_2

action_flag_1 = True
action_flag_2 = True
last_action_time_1 = datetime.datetime.now()
last_action_time_2 = datetime.datetime.now()

# Init Encryption settings
key = "thisismysecretky"
key = bytes(str(key), encoding="utf8")

class DataServer:
    global action_flag_1
    global action_flag_2
    def __init__(self, HOST, PORT):
        while True:
            try:
                self.HOST = HOST
                self.PORT = PORT
                self.serverSocket = socket(AF_INET, SOCK_STREAM)
                self.serverSocket.bind((HOST,PORT))
                self.client_sockets = []
                break
            except BrokenPipeError:
                sleep(0.1)

    def send_to_relay(self, message):
        encodedMessage = message.encode()
        # Encrypt data
        cipher = AES.new(key, AES.MODE_CBC)
        encryptedMessage = cipher.iv + cipher.encrypt(pad(encodedMessage, AES.block_size))
        encryptedMessage_64 = b64encode(encryptedMessage)
        len_byte = str(len(encryptedMessage_64)).encode("utf-8") + b'_'
        finalmsg = len_byte+encryptedMessage_64

        # Send to all clients
        for client_socket in self.client_sockets:
            client_socket.send(finalmsg)

    # Thread to receive the message
    def thread_DataServer_Receiver(self,connSocket, clientAddr):
        global action_flag_1
        global action_flag_2
        global last_action_time_1
        global last_action_time_2
        while True:
            # Receive and Parse message (len_EncryptedMessage)
            # recv length followed by '_' followed by cypher
            message = b''
            while not message.endswith(b'_'):
                _d = connSocket.recv(1)
                if not _d:
                    message = b''
                    break
                message += _d
            if len(message) == 0:
                print('no more data from the client')
                self.serverSocket.close()
                return

            message = message.decode("utf-8")
            length = int(message[:-1])
            message = b''
            while len(message) < length:
                _d = connSocket.recv(length - len(message))
                if not _d:
                    message = b''
                    break
                message += _d
            if len(message) == 0:
                print('no more data from the client')
                self.serverSocket.close()
                return
            decodedMessage = b64decode(message)

            iv = decodedMessage[:AES.block_size]
            cipher = AES.new(key, AES.MODE_CBC, iv)
            decryptedMessage = cipher.decrypt(decodedMessage[16:])
            decryptedMessage = unpad(decryptedMessage, AES.block_size)
            decryptedMessage = decryptedMessage.decode()
            x = decryptedMessage.split()
            if(x[0] == "vest"):
                vest_one_queue.append(1) if x[1] == '0' else vest_two_queue.append(1)
            elif(x[0] == "gun"):
                gun_one_queue.append(1) if x[1] == '0' else  gun_two_queue.append(1) 
            else:
                unpacked = eval(x[1])
                if x[0] == '0':
                    motion_one_queue.append(unpacked)
                    action_flag_1 = False
                    last_action_time_1 = datetime.datetime.now()
                    
                else:
                    motion_two_queue.append(unpacked)
                    action_flag_2 = False
                    last_action_time_2 = datetime.datetime.now()
            

    # Data Server Thread
    def thread_DataServer(self):
        # Listens for incoming connections
        self.serverSocket.listen()
        print("Data Server is ready to receive message")

        try:
            while True:
                # Upon successful connection with a client socket, spawns a new thead
                connSocket, clientAddr = self.serverSocket.accept()
                self.client_sockets.append(connSocket)
                print("Connected to ", clientAddr)
                serverThread = Thread(target=self.thread_DataServer_Receiver, args=(connSocket, clientAddr))
                serverThread.start()
        except KeyboardInterrupt:
            print("Closing socket")
            self.serverSocket.close()

class HardwareAI:

    def __init__(self, player):
        self.player = player
        self.count = 0

    def add_to_csv(self):

        fieldnames = [
        "roll" ,
        "pitch",
        "yaw"  ,
        "accX" ,
        "accY" ,
        "accZ" 
        ]
        queue = motion_one_queue if self.player == 1 else motion_two_queue

        if len(queue) < 30:
            print("function submit_input: input length is less than 30")
            return []
        
        ave_queue = []
        for i in range(len(queue)-20, len(queue)):
            ave_queue.append(queue[i])
        
        with open('./shield.csv', 'a', encoding='UTF8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)

            for data in ave_queue:
                dick = dict(zip(fieldnames, data))
                writer.writerow(dick)
        
        print("added to csv ", self.count)
        self.count += 1


    def thread_hardware_ai(self):
        global motion_one_queue
        global motion_two_queue
        global action_flag_1
        global action_flag_2
        while True:
            # Check if last action exceeds 0.5s
            if (datetime.datetime.now() - last_action_time_1).total_seconds() >= 0.5:
                action_flag_1 = True

            if action_flag_1 and len(motion_one_queue) < 30:
                motion_one_queue.clear()

            # Predict action if buffer has sufficient data
            if self.player == 1 and action_flag_1 and len(motion_one_queue) >= 30:
                action_classified = self.add_to_csv()
                motion_one_queue.clear()
                if action_classified != "nil":
                    action_one_queue.append(action_classified)
            

# Init global objects
ds = DataServer(DATA_HOST, DATA_PORT)
ai1 = HardwareAI(player=1)

def main():
    data_server_thread = Thread(target=ds.thread_DataServer)
    hardware_ai_p1_thread = Thread(target=ai1.thread_hardware_ai)

    # eval_server_thread.start()
    data_server_thread.start()
    hardware_ai_p1_thread.start()

    


if __name__ == "__main__":
    main()
