from socket import *
import threading as t
from base64 import b64decode
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

# Init connection settings
HOST = gethostname()
PORT = 8080

# Init Encryption settings
key = "thisismysecretky"
key = bytes(str(key), encoding="utf8")  

# Thread to receive the message and echo back message 
def thread(connSocket, clientAddr):
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
        print("Received message from ", clientAddr, ": ", decryptedMessage)

def main():
    # Create server socket and bind to host and port
    serverSocket = socket(AF_INET, SOCK_STREAM)
    serverSocket.bind((HOST,PORT))

    # Listens for incoming connections
    serverSocket.listen()
    print("Server is ready to receive message")

    try:
        while True:
            # Upon successful connection with a client socket, spawns a new thead
            connSocket, clientAddr = serverSocket.accept()
            print("Connected to ", clientAddr)
            serverThread = t.Thread(target=thread, args=(connSocket, clientAddr))
            serverThread.start()
    except KeyboardInterrupt:
        print("Closing socket")
        serverSocket.close()


if __name__ == "__main__":
    main()