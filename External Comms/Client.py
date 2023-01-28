from socket import *
import time

HOST = "localhost"
PORT = 8888

clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.connect((HOST, PORT))

i = 0
try:
    while True:
        message = str(i)
        clientSocket.send(message.encode())

        receivedMsg = clientSocket.recv(2048)

        print("From Server: ", receivedMsg.decode())

        time.sleep(1)

        i+=1
except KeyboardInterrupt:
    print("Closing Client Socket")
    clientSocket.close()    