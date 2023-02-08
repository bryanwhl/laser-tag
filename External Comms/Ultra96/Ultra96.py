from socket import *
import threading as t
from base64 import b64encode, b64decode
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import json
import random

# Init connection settings
DATA_HOST = gethostname()
DATA_PORT = 8080

EVAL_HOST = "192.168.95.247"
EVAL_PORT = 1515

# Init Queues
messageQueue = []

# Init Encryption settings
key = "thisismysecretky"
key = bytes(str(key), encoding="utf8") 

# Dummy Game status data
data_json = {
            "p1": {
                "hp": 10,
                "action": "grenade",
                "bullets": 1,
                "grenades": 1,
                "shield_time": 0,
                "shield_health": 3,
                "num_deaths": 1,
                "num_shield": 0
            },
            "p2": {
                "hp": 100,
                "action": "shield",
                "bullets": 2,
                "grenades": 2,
                "shield_time": 1,
                "shield_health": 0,
                "num_deaths": 5,
                "num_shield": 2
            }
        }

actions = ['shoot', 'grenade', 'shield', 'logout']

class DataServer:
    def __init__(self, HOST, PORT):
        self.HOST = HOST
        self.PORT = PORT
        self.serverSocket = socket(AF_INET, SOCK_STREAM)
        self.serverSocket.bind((HOST,PORT))


    # Thread to receive the message
    def thread_DataServer_Receiver(self,connSocket, clientAddr):
        while True:
            # Receive data
            message = connSocket.recv(2048)       
            if not message:
                connSocket.close()
                return
            # Decrypt data
            decodedMessage = b64decode(message)
            iv = decodedMessage[:AES.block_size]

            cipher = AES.new(key, AES.MODE_CBC, iv)
            decryptedMessage = cipher.decrypt(decodedMessage[16:])
            decryptedMessage = unpad(decryptedMessage, AES.block_size)
            decryptedMessage = decryptedMessage.decode()
            messageQueue.append(decryptedMessage)
            print("Received message from ", clientAddr, ": ", decryptedMessage)

    # Data Server Thread
    def thread_DataServer(self):
        # Listens for incoming connections
        self.serverSocket.listen()
        print("Server is ready to receive message")

        try:
            while True:
                # Upon successful connection with a client socket, spawns a new thead
                connSocket, clientAddr = self.serverSocket.accept()
                print("Connected to ", clientAddr)
                serverThread = t.Thread(target=self.thread_DataServer_Receiver, args=(connSocket, clientAddr))
                serverThread.start()
        except KeyboardInterrupt:
            print("Closing socket")
            self.serverSocket.close()

class EvalClient:
    def __init__(self, HOST, PORT):
        self.HOST = HOST
        self.PORT = PORT
        self.clientSocket = socket(AF_INET, SOCK_STREAM)
        self.clientSocket.connect((HOST, PORT))

    # Eval Client Thread
    def thread_EvalClient(self):
        try:
            while True:
                # Check if messageQueue has any messages
                while messageQueue:
                    # Create random action
                    ind = random.randint(0,3)
                    print("Action: ", actions[ind])
                    message = json.dumps(data_json)
                    encodedMessage = message.encode()
                    # Encrypt data
                    cipher = AES.new(key, AES.MODE_CBC)
                    encryptedMessage = cipher.iv + cipher.encrypt(pad(encodedMessage, AES.block_size))
                    encryptedMessage_64 = b64encode(encryptedMessage)
                    len_byte = str(len(encryptedMessage_64)).encode("utf-8") + b'_'
                    finalmsg = len_byte+encryptedMessage_64
                    # Send data
                    self.clientSocket.send(finalmsg)
                    # Pop from messageQueue
                    messageQueue.pop(0)
        except KeyboardInterrupt:
            print("Closing Client Socket")
            self.clientSocket.close()  

def main():
    ds = DataServer(DATA_HOST, DATA_PORT)
    ec = EvalClient(EVAL_HOST, EVAL_PORT)

    dataServerThread = t.Thread(target=ds.thread_DataServer)
    evalServerThread = t.Thread(target=ec.thread_EvalClient)

    dataServerThread.start()
    evalServerThread.start()
    


if __name__ == "__main__":
    main()