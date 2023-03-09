import sys
import time
import socket
from socket import *
from threading import Thread
import crc8
from bluepy import btle
from bluepy.btle import BTLEException, Peripheral
from datetime import datetime
from math import floor
from queue import Queue
from signal import signal, SIGPIPE, SIG_DFL  
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from base64 import b64encode, b64decode

signal(SIGPIPE,SIG_DFL) 

# Init connection settings
HOST = "localhost"
PORT = 8888

# Init Encryption settings
key = "thisismysecretky"
key = bytes(str(key), encoding="utf8") 

#variables for beetle
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
    "B0:B1:13:2D:D8:8C",
    "B0:B1:13:2D:D4:89",
    "B0:B1:13:2D:B3:08",
    "B0:B1:13:2D:D8:AC",
    "B0:B1:13:2D:CD:A2"
    ]
beetle_status = {}
PACKET_LENGTH = 20

#constants for print formatting
CR = "\r"
SPACE = "            "
END = ""


#variables for data rate and fragmentation statistics
program_start_time = datetime.now()
total_bytes_obtained = 0
total_packet = 0
total_packet_processed = 0

#for external comms
motion_msg = Queue(maxsize = 1269)
vest_msg = Queue(maxsize = 1269)
gun_msg = Queue(maxsize = 1269)

hp_one = []
hp_two = []
bullet_one = []
bullet_two = []

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
                print('no more data from Ultra96')
                self.serverSocket.close()
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
                print('no more data from Ultra96')
                self.serverSocket.close()
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
        print("connecting to server...")
        self.clientSocket = socket(AF_INET, SOCK_STREAM)
        # Create client socket and connect to server
        self.clientSocket = socket(AF_INET, SOCK_STREAM)
        self.clientSocket.connect((HOST, PORT))

        # Create thread to receive from Ultra96
        receiver_thread = Thread(target=self.receive_from_ultra, args=(self.clientSocket,))
        receiver_thread.start()

        print("connected to server...")
        try:
            while True:
                if not vest_msg.empty():
                    message = "vest " + str(vest_msg.get())
                    encodedMessage = message.encode()
                    # Encrypt data
                    cipher = AES.new(key, AES.MODE_CBC)
                    encryptedMessage = cipher.iv + cipher.encrypt(pad(encodedMessage, AES.block_size))
                    encryptedMessage_64 = b64encode(encryptedMessage)
                    len_byte = str(len(encryptedMessage_64)).encode("utf-8") + b'_'
                    finalmsg = len_byte+encryptedMessage_64
                    self.clientSocket.send(finalmsg)
                    time.sleep(0.05)
                    
                if not gun_msg.empty():
                    message = "gun " + str(gun_msg.get())
                    encodedMessage = message.encode()
                    # Encrypt data
                    cipher = AES.new(key, AES.MODE_CBC)
                    encryptedMessage = cipher.iv + cipher.encrypt(pad(encodedMessage, AES.block_size))
                    encryptedMessage_64 = b64encode(encryptedMessage)
                    len_byte = str(len(encryptedMessage_64)).encode("utf-8") + b'_'
                    finalmsg = len_byte+encryptedMessage_64
                    self.clientSocket.send(finalmsg)
                    time.sleep(0.05)
                    
                if not motion_msg.empty():
                    message = str(motion_msg.get())
                    encodedMessage = message.encode()
                    # Encrypt data
                    cipher = AES.new(key, AES.MODE_CBC)
                    encryptedMessage = cipher.iv + cipher.encrypt(pad(encodedMessage, AES.block_size))
                    encryptedMessage_64 = b64encode(encryptedMessage)
                    len_byte = str(len(encryptedMessage_64)).encode("utf-8") + b'_'
                    finalmsg = len_byte+encryptedMessage_64
                    self.clientSocket.send(finalmsg)
                    time.sleep(0.05)            
        except KeyboardInterrupt:
            print("Closing Client Socket")
            self.clientSocket.close() 
            sys.exit(1)

class MyDelegate(btle.DefaultDelegate):
    def __init__(self, connection_index):
        btle.DefaultDelegate.__init__(self)
        self.connection_index = connection_index
        self.ID = str(connection_index)
        self.buffer = ""
        self.packet_processed = 0
        self.packet_total = 0

    def handleNotification(self, cHandle, data):
        
        #add received data to buffer
        self.buffer += clean_data(str(data))
        self.packet_total += 1
        
        global total_packet
        global total_packet_processed
        global total_bytes_obtained
        global program_start_time
        total_packet += 1
        
        global vest_msg
        global gun_msg
        
        connection_threads[self.connection_index].total_data_received += utf8len(str(data))
        total_bytes_obtained += utf8len(str(data))
        
        if(len(self.buffer) >= PACKET_LENGTH):
            self.packet_processed += 1
            total_packet_processed += 1
            data_string = self.buffer[:PACKET_LENGTH]
            #print("data_string used: ", data_string)
            self.buffer = self.buffer[PACKET_LENGTH:]
            if crc_check(data_string):
                #process incoming packet
                BEETLE_ID = data_string[0]
                PACKET_ID = data_string[1]
                DATA = clear_padding(data_string[2:-2])
                print(CR, "data from ", BEETLE_ID, end = END)
                
                #(BEETLE_ID == self.ID) and 
                
                #update last sync time that is used for wakeup/timeout calls
                connection_threads[self.connection_index].last_sync_time = datetime.now()
                
                #handle packet from beetle
                if ((PACKET_ID == '0') and (DATA == "ACK")):
                    #print(CR, "ACK received", SPACE, end = END)
                    connection_threads[self.connection_index].ACK = True
                elif ((PACKET_ID == '1') and (DATA == "HANDSHAKE")):
                    print(CR, "Handshake reply received", SPACE, end = END)
                    connection_threads[self.connection_index].handshake_reply = True
                elif ((PACKET_ID == '2') and (DATA == "WAKEUP")):
                    #print(CR, "Wakeup reply received", SPACE, end = END)
                    connection_threads[self.connection_index].ACK = True
                elif ((PACKET_ID == '3') and (DATA[1:] == "GUN")):
                    connection_threads[self.connection_index].send_ack = True
                    connection_threads[self.connection_index].rcv_seq_num = DATA[0]
                    if(DATA[0] == str(connection_threads[self.connection_index].seq_num)):
                        connection_threads[self.connection_index].correct_seq_num = True
                        gun_msg.put(floor(self.connection_index/3))
                        print(CR, "Player has fired a shot", SPACE)
                    else:
                        connection_threads[self.connection_index].correct_seq_num = False
                elif ((PACKET_ID == '4') and (DATA[1:] == "VEST")):
                    connection_threads[self.connection_index].send_ack = True
                    connection_threads[self.connection_index].rcv_seq_num = DATA[0]
                    if(DATA[0] == str(connection_threads[self.connection_index].seq_num)):
                        connection_threads[self.connection_index].correct_seq_num = True
                        vest_msg.put(floor(self.connection_index/3))
                        print(CR, "Player has been hit", SPACE)
                    else:
                        connection_threads[self.connection_index].correct_seq_num = False
                elif ((PACKET_ID == '5')):
                    #print(CR, "Motion sensor data packet 1 obtained", SPACE, end = END)
                    extracted_data = unpack_data(DATA)
                    #print(extracted_data[0], " ", extracted_data[1], " ", extracted_data[2])
                    if (connection_threads[self.connection_index].handshake_completed):
                        connection_threads[self.connection_index].packet_0 = True
                        connection_threads[self.connection_index].packet_0_rcv_time = datetime.now()
                        connection_threads[self.connection_index].current_data["roll"] = extracted_data[0]
                        connection_threads[self.connection_index].current_data["pitch"] = extracted_data[1]
                        connection_threads[self.connection_index].current_data["yaw"] = extracted_data[2]
                elif ((PACKET_ID == '6')):
                    #print(CR, "Motion sensor data packet 2 obtained", SPACE, end = END)
                    extracted_data = unpack_data(DATA)
                    #print(extracted_data[0], " ", extracted_data[1], " ", extracted_data[2])
                    if (connection_threads[self.connection_index].handshake_completed):
                        connection_threads[self.connection_index].packet_1 = True
                        connection_threads[self.connection_index].packet_1_rcv_time = datetime.now()
                        connection_threads[self.connection_index].current_data["accX"] = extracted_data[0]      
                        connection_threads[self.connection_index].current_data["accY"] = extracted_data[1]   
                        connection_threads[self.connection_index].current_data["accZ"] = extracted_data[2] 
                    
                            
            else:
                print(CR, "ERR in CRC", SPACE, end = END)
                self.buffer = ""
                connection_threads[self.connection_index].error = True
                time.sleep(0.01)

def clean_data(info):
    return (info[2:-1])

def clear_padding(data):
    while True:
        if (data[0] == '#'):
            data = data[1:]
        else:
            return data

def unpack_data(data):
    signs   = int(data[0])
    value_1 = int(data[1:6]) / 100
    value_2 = int(data[6:11]) / 100
    value_3 = int(data[11:16]) / 100
    if (signs % 2 != 0):
        value_3 = -value_3
    if ((signs/2) % 2 != 0):
        value_2 = -value_2
    if ((floor(signs/2)/2) % 2 != 0):
        value_1 = -value_1
    return value_1, value_2, value_3

def utf8len(s):
    return len(s.encode('utf-8'))

def crc_check(data_string):
    hash = crc8.crc8()
    crc = data_string[-2:]
    data_string = data_string[2:-2]
    hash.update(bytes(data_string, "utf-8"))
    if (hash.hexdigest() == crc):
        return True
    else:
        return False

class BeetleThread(Thread):
    start_time = datetime.now()
    last_sync_time = start_time
    current_time = start_time
    handshake_reply = False
    handshake_completed = False
    ACK = False
    packet_0 = False
    packet_1 = False
    packet_0_rcv_time = start_time
    packet_1_rcv_time = start_time
    total_data_received = 0
    error = False
    seq_num = 0
    send_ack = False
    correct_seq_num = False
    rcv_seq_num = "x"
    err_count = 0
    current_data = {
        "id"    : "#",
        "roll"  : "#",
        "pitch" : "#",
        "yaw"   : "#",
        "accX"  : "#",
        "accY"  : "#",
        "accZ"  : "#",
    }

    def __init__(self, connection_index, addr):
        Thread.__init__(self)
        self.connection_index = connection_index
        self.addr = addr
        self.current_data["id"] = str(floor(connection_index/3))

    def run(self):
        global motion_msg
        self.establish_connection()
        time.sleep(2.0)
        try:
            # handshake at start of thread
            self.handshake(self.pheripheral)
            
            while True:
                self.current_time = datetime.now()
                time_diff = self.current_time - self.last_sync_time
                if (time_diff.total_seconds() > 60):
                    self.wakeup(self.pheripheral)

                # call data collecting comms
                self.receive_data(self.pheripheral, motion_msg)

        except BTLEException:
            self.pheripheral.disconnect()
            # start a function to create new thread after reconnecting
            reconnect = Thread(target=reconnection(
                self.addr, self.connection_index))
            reconnect.start()
            # end current thread to reset everything as new one will be started after reconnection
            sys.exit(1)
        
        except KeyboardInterrupt:
            self.pheripheral.disconnect()
            sys.exit(1)
            

    def handshake(self, p):
        while (not self.handshake_reply):
            count = 0
            # Send handshake packet
            self.send_data("H")
            print("HANDSHAKE SENT")
            # Wait for Handshake packet from bluno, sent handshake req agn if not received after some time
            while(count < 5):
                p.waitForNotifications(1)
                time.sleep(0.1)
                count += 1
                if(self.handshake_reply):
                    break
        # Send back 
        print("HANDSHAKE RECEIVED, RETURN ACK")
        self.send_data("A")
        self.handshake_reply = False
        count = 0
        
        #wait incase there is retransmission of handshake by beetle
        while(count < 6):
            p.waitForNotifications(0.2)
            if(self.handshake_reply):
                count = 0
                self.send_data("A")
                self.handshake_reply = False
            count += 1
        self.handshake_completed = True
        time.sleep(2.0)
        self.start_time = datetime.now()

    def wakeup(self, p):
        count = 0
        print(CR, "WAKE UP CALL", SPACE, end = END)
        # Wait for ack packet from bluno
        while (not self.ACK):
            self.send_data("W")
            p.waitForNotifications(0.5)
            count += 1
            if(count >= 7):
                raise BTLEException("BEETLE NOT WAKING UP ZZZ")
        print(CR, "WAKEUP ACKED", SPACE, end = END)
        self.ACK = False

    def receive_data(self, p, queue):
        #data will expire and be unusable after some time
        if(self.current_time - self.packet_0_rcv_time).total_seconds() > 0.2:
            self.packet_0 = False
        if(self.current_time - self.packet_1_rcv_time).total_seconds() > 0.2:
            self.packet_1 = False
            
        # some loops to ensure all packets are received
        for x in range(2):
            p.waitForNotifications(0.1)
        
        #for stop and wait
        if(self.send_ack):
            self.acknowledge_data()
            self.send_ack = False
            
        #if there is error in crc
        if self.error:
            if (self.err_count > 8):
                raise BTLEException("CONTINUOUS FAIL CRC :(")
            self.err_count = self.err_count+1
            self.error = False
            
        #if both halves of packet is received and both halves are close to each other (not necessarily same data set)
        if self.packet_0 and self.packet_1 and abs((self.packet_1_rcv_time - self.packet_0_rcv_time).total_seconds()) < 0.2:
            print(CR, self.current_data, SPACE, end = END)
            queue.put(self.current_data)
            
            #each data can only be used once
            self.packet_0 = False
            self.packet_1 = False
            
    def update_beetles(self, p):
        global hp_value_p1
        global hp_value_p2
        global bullet_count_p1
        global bullet_count_p2
        if(self.addr == "B0:B1:13:2D:D8:8C" and bullet_count_p1):   # gun 1
            count = 0
            print(CR, "UPDATING GUN STATUS", SPACE, end = END)
            # Wait for ack packet from bluno
            while (not self.ACK):
                self.send_data("R")
                p.waitForNotifications(0.5)
                count += 1
                if(count >= 5):
                    raise BTLEException("BEETLE NOT RESPONDING ZZZ")
            print(CR, "UPDATE ACKED", SPACE, end = END)
            reload_flags[0] = False
            self.ACK = False
        elif(self.addr == "B0:B1:13:2D:CD:A2"): # gun 2
            if(reload_flags[1] == True):
                count = 0
                print(CR, "UPDATING GUN STATUS", SPACE, end = END)
                # Wait for ack packet from bluno
                while (not self.ACK):
                    self.send_data("R")
                    p.waitForNotifications(0.5)
                    count += 1
                    if(count >= 5):
                        raise BTLEException("BEETLE NOT RESPONDING ZZZ")
                print(CR, "UPDATE ACKED", SPACE, end = END)
                reload_flags[1] = False
                self.ACK = False
        elif(self.addr == "B0:B1:13:2D:D4:89"): # vest 1
            if(hp_flags[0] == True):
                count = 0
                print(CR, "UPDATING GUN STATUS", SPACE, end = END)
                # Wait for ack packet from bluno
                while (not self.ACK):
                    if(hp_value[0] >= 70):
                        self.send_data("h")
                    elif(hp_value[0] >= 40):
                        self.send_data("m")
                    else:
                        self.send_data("l") 
                    p.waitForNotifications(0.5)
                    count += 1
                    if(count >= 5):
                        raise BTLEException("BEETLE NOT RESPONDING ZZZ")
                print(CR, "UPDATE ACKED", SPACE, end = END)
                hp_flags[0] = False
                self.ACK = False
        elif(self.addr == "B0:B1:13:2D:D8:AC"): # vest 2
            if(hp_flags[0] == True):
                count = 0
                print(CR, "UPDATING GUN STATUS", SPACE, end = END)
                # Wait for ack packet from bluno
                while (not self.ACK):
                    if(hp_value[0] >= 70):
                        self.send_data("h")
                    elif(hp_value[0] >= 40):
                        self.send_data("m")
                    else:
                        self.send_data("l") 
                    p.waitForNotifications(0.5)
                    count += 1
                    if(count >= 5):
                        raise BTLEException("BEETLE NOT RESPONDING ZZZ")
                print(CR, "UPDATE ACKED", SPACE, end = END)
                hp_flags[0] = False
                self.ACK = False
            
    def acknowledge_data(self):
        print(CR, "DATA RECEIVED. ACK SENT", SPACE, end = END)
        self.send_data(self.rcv_seq_num)
        if(self.correct_seq_num and self.seq_num == 1):
            self.seq_num = 0
        elif(self.correct_seq_num and self.seq_num == 0):
            self.seq_num = 1
            
    def data_rate(self):
        kbps = (self.total_data_received * 8) / (1000 * (datetime.now() - self.start_time).total_seconds())
        print(" Data rate(kbps):", round(kbps, 6), SPACE, end = END)
        
    def send_data(self, message):
        for characteristic in self.characteristic:
                characteristic.write(bytes(message, "UTF-8"), withResponse=False)
        
    def establish_connection(self):
        while True:
            try:
                print("CONNECTING TO ", self.addr)
                
                self.pheripheral = Peripheral(self.addr)
                beetle_status[self.connection_index] = self.pheripheral
                self.service = self.pheripheral.getServices()
                self.characteristic = self.pheripheral.getCharacteristics()
                self.pheripheral.setDelegate(MyDelegate(self.connection_index))
                print("CONNECTED TO ", self.addr)
                
                break
            except BTLEException:
                time.sleep(3)


def reconnection(addr, index):
    while True:
        try:
            print(CR, "RECONNECTING %s" % (addr), SPACE, end = END)
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
        print("Closing connections")

if __name__ == "__main__":
    main()