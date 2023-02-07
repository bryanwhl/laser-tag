from socket import *
import time
import json
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from base64 import b64encode

# Init connection settings
HOST = "192.168.95.247"
PORT = 1515

# Init Encryption settings
key = "thisismysecretky"
key = bytes(str(key), encoding="utf8") 

# Create client socket and connect to server
clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.connect((HOST, PORT))

# Send message to server upon pressing key
try:
    while True:
        # Wait for user input
        input()

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
        data_str = json.dumps(data_json)
        data_bytes = data_str.encode()
        # Encrypt data
        cipher = AES.new(key, AES.MODE_CBC)
        encrypted_data = cipher.iv + cipher.encrypt(pad(data_bytes, AES.block_size))
        encrypted_data_b64 = b64encode(encrypted_data)
        len_byte = str(len(encrypted_data_b64)).encode("utf-8") + b'_'
        finalmsg = len_byte+encrypted_data_b64
        clientSocket.send(finalmsg)
except KeyboardInterrupt:
    print("Closing Client Socket")
    clientSocket.close()    