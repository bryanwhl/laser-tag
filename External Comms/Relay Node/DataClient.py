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
    while True:
        data = "this is the data"
        data_bytes = data.encode()
        # Encrypt data
        cipher = AES.new(key, AES.MODE_CBC)
        encrypted_data = cipher.iv + cipher.encrypt(pad(data_bytes, AES.block_size))
        encrypted_data_b64 = b64encode(encrypted_data)
        clientSocket.send(encrypted_data_b64)
        time.sleep(0.1)
except KeyboardInterrupt:
    print("Closing Client Socket")
    clientSocket.close()    