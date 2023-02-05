import sys
import time
from threading import Thread
import crc8
from bluepy import btle
from bluepy.btle import BTLEException, Peripheral
from datetime import datetime

service_uuid = "0000dfb0-0000-1000-8000-00805f9b34fb"

connection_threads = {}
address = "B0:B1:13:2D:CD:A2"
beetle_addresses = ["B0:B1:13:2D:CD:A2"]
beetle_status = {}


#https://careerkarma.com/blog/python-string-to-int/
class MyDelegate(btle.DefaultDelegate):
    def __init__(self, connection_index):
        btle.DefaultDelegate.__init__(self)
        self.connection_index = connection_index
        self.ID=str(connection_index)

    def handleNotification(self, cHandle, data):
        data_string = clean_data(str(data))
        print(data)
        if crc_check(data_string):
            BEETLE_ID = data_string[0]
            PACKET_ID = data_string[1]
            DATA = clear_padding(data_string[2:-2])
            if ((BEETLE_ID == self.ID) and (PACKET_ID == '0') and (DATA == "ACK")):
                connection_threads[self.connection_index].ACK=True
            if ((BEETLE_ID == self.ID) and (PACKET_ID == '1') and (DATA == "HANDSHAKE")): 
                connection_threads[self.connection_index].handshake=True
            if ((BEETLE_ID == self.ID) and (PACKET_ID == '2') and (DATA == "GUN")): 
                print("Player has fired a shot")
            if ((BEETLE_ID == self.ID) and (PACKET_ID == '3') and (DATA == "VEST")): 
                print("Player has been hit")
            if ((BEETLE_ID == self.ID) and (PACKET_ID == '4')): 
                print("motion sensor data obtained")
            if ((BEETLE_ID == self.ID) and (PACKET_ID == '5') and (DATA == "WAKEUP")): 
                connection_threads[self.connection_index].ACK=True
            '''
            if ((BEETLE_ID == self.ID) and (PACKET_ID == '3')):
                text = DATA.split("|")
                connection_threads[self.connection_index].current_data["roll"]=text[0]
                connection_threads[self.connection_index].current_data["pitch"]=text[1]
            if ((BEETLE_ID == self.ID) and (PACKET_ID == '4')):
                text = DATA.split("|")
                connection_threads[self.connection_index].current_data["yaw"]=text[0]
                connection_threads[self.connection_index].current_data["AccX"]=text[1]
            if ((BEETLE_ID == self.ID) and (PACKET_ID == '5')):
                text = DATA.split("|")
                connection_threads[self.connection_index].current_data["AccY"]=text[0]
                connection_threads[self.connection_index].current_data["AccZ"]=text[1]
            '''
        else:
            print("ERR in CRC")
            time.sleep(0.01)


#data processing for incoming packets
def clean_data(info):
    return(info[2:-1])

#remove padded '#' from message
def clear_padding(data):
    while True:
        if (data[0] == '#'):
            data = data[1:]
        else:
            return data
        
#CRC check https://pypi.org/project/crc8/
def crc_check(data_string):
    hash = crc8.crc8()
    crc = data_string[-2:]
    data_string = data_string[2:-2]
    hash.update(bytes(data_string, "utf-8"))
    if (hash.hexdigest() == crc):
        return True
    else:
        return False

# Thread generation for each beetle
# to use for timeout to trigger sending of wakeup call https://pynative.com/python-get-time-difference/
class BeetleThread(Thread):
    last_sync_time = datetime.now().strftime("%H:%M:%S")
    handshake = False
    ACK = False
    clear =False
    sync =False
    millis=0
    err_count=0
    current_data={
        "roll" : "#",
        "pitch" : "#",
        "yaw" : "#",
        "AccX" : "#",
        "AccY" : "#",
        "AccZ" : "#",
    }

    def __init__(self,connection_index, addr, reconnect):
        print("connected to",addr,"\n")
        Thread.__init__(self)
        self.connection_index = connection_index
        self.addr = addr
        self.connection = (beetle_status[self.connection_index])
        self.connection.setDelegate(MyDelegate(self.connection_index))
        self.reconnect=reconnect
        self.service=self.connection.getServiceByUUID(service_uuid)
        self.characteristic=self.service.getCharacteristics()[0]
        self.global_counter = 0
        
    def run(self):
        
        #handshake at start of thread
        self.handshake(self.connection)
        
        while True:
            
                    # convert time string to datetime
            t1 = datetime.strptime(self.last_sync_time, "%H:%M:%S")
            t2 = datetime.strptime(datetime.now().strftime("%H:%M:%S"), "%H:%M:%S")
            delta = t2 - t1
            if(delta.total_seconds() > 60):
                self.wakeup(self.connection)
            
            if (self.reconnect):
                time.sleep(1)
                print("reconnect")
                self.clear_proto(self.connection)
            try:
                if (self.connection_index==0):
                    #call data collecting comms
                    self.receive_data(self.connection)
                else:
                    #call position collectiog comms
                    self.pos_proto(self.connection)
            except BTLEException:
                # enter when disconnected
                self.connection.disconnect()
                #start a function to create new thread after reconnecting
                reconnect = Thread(target=reconnection(self.addr,self.connection_index))
                reconnect.start()
                #end current thread as new one will be started after reconnection
                sys.exit(1)

    def clear_proto(self,p):
        while not self.handshake:
            self.characteristic.write(bytes("H", "utf-8"), withResponse=False)
            # Wait for Handshake packet from bluno 
            p.waitForNotifications(0.01)
        self.handshake=False

    def handshake(self,p):
        # Send handshake packet
        print("HANDSHAKE SENT")
        self.characteristic.write(bytes("H", "utf-8"), withResponse=False)
        # Wait for Handshake packet from bluno 
        while (not self.handshake):
            p.waitForNotifications(2)
        self.handshake=False
        # Send back ACK
        print("HANDSHAKE RECIEVED, RETURN ACK")
        while (not self.ACK):
            time.sleep(0.5)
            self.characteristic.write(bytes("A", "utf-8"), withResponse=False)
            p.waitForNotifications(2)
        self.ACK=False
        
    def wakeup(self, p):
        # Send handshake packet
        print("WAKE UP CALL")
        self.characteristic.write(bytes("W", "utf-8"), withResponse=False)
        # Wait for ack packet from bluno 
        while (not self.ACK):
            p.waitForNotifications(2)
        self.ACK=False
            
    def receive_data(self,p):
        error = False
        # recieve info for current data set
        while True:
            self.current_data={
                "roll" : "#",
                "pitch" : "#",
                "yaw" : "#",
                "AccX" : "#",
                "AccY" : "#",
                "AccZ" : "#",
                "millis" : "#"
            }
            #some loops to ensure all packets supposed to be recieved     
            for x in range(6):
                p.waitForNotifications(0.1)
                # print(self.current_data)
                if (self.current_data["millis"]!='#'):
                        break  
            if error:
                if (self.err_count>8):
                    raise BTLEException("error")
                self.err_count=self.err_count+1
                error = False
                continue
            self.err_count=0
            self.characteristic.write(bytes("A", "utf-8"), withResponse=False)

def establish_connection():
    print("Connecting to bluno ...")
    for i in range(len(beetle_addresses)):
        print(i)
        p = Peripheral(beetle_addresses[i])
        beetle_status[i]=p
        print(i)
        print(beetle_status[i])
        t = BeetleThread(i, beetle_addresses[i], False)
        #start thread
        t.start()
        connection_threads[i]=t

def reconnection(addr,index):
        print("reconnecting bluno")
        while True:
            try:
                print("reconnecting to %s" % (addr))
                p = btle.Peripheral(addr)
                print("re-connected to %s" % (addr))
                beetle_status[index]=p
                t = BeetleThread(index, addr, True)
                #start thread
                t.start()
                connection_threads[index]=t
                break
            except Exception:
                time.sleep(1)
                continue

def main():
    establish_connection()

if __name__ == "__main__":
    main()