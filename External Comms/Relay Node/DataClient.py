from socket import *
import time
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from base64 import b64encode

# Init connection settings
HOST = "localhost"
PORT = 8888

# Init Encryption settings
key = "thisismysecretky"
key = bytes(str(key), encoding="utf8") 

# Create client socket and connect to server
clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.connect((HOST, PORT))

# Send message to server every 0.1 second
try:
    i = 0
    while True:
        input()
        message = str(i)
        encodedMessage = message.encode()
        # Encrypt data
        cipher = AES.new(key, AES.MODE_CBC)
        encryptedMessage = cipher.iv + cipher.encrypt(pad(encodedMessage, AES.block_size))
        encryptedMessage_64 = b64encode(encryptedMessage)
        clientSocket.send(encryptedMessage_64)
        i+=1

except KeyboardInterrupt:
    print("Closing Client Socket")
    clientSocket.close()    
