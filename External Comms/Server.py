from socket import *
import threading as t

HOST = gethostname()
PORT = 8888

def thread(connSocket, clientAddr):
    while True:
        message = connSocket.recv(2048)
        if not message:
            connSocket.close()
            return
        print("Received message from ", clientAddr, ": ", message)
        connSocket.send(message)
        

def main():
    serverSocket = socket(AF_INET, SOCK_STREAM)
    serverSocket.bind((HOST,PORT))

    serverSocket.listen()
    print("Server is ready to receive message")

    try:
        while True:
            connSocket, clientAddr = serverSocket.accept()
            print("Connected to ", clientAddr)
            serverThread = t.Thread(target=thread, args=(connSocket, clientAddr))
            serverThread.start()
    except KeyboardInterrupt:
        print("Closing socket")
        serverSocket.close()


if __name__ == "__main__":
    main()