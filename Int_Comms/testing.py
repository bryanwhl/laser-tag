import sys
import time
from threading import Thread
import crc8
from bluepy import btle
from bluepy.btle import BTLEException, Peripheral

service_uuid = "0000dfb0-0000-1000-8000-00805f9b34fb"

connection_threads = {}
connected_addr=[]
main_data={} 

address = "B0:B1:13:2D:CD:A2"
beetle_addresses = ["B0:B1:13:2D:CD:A2"]
beetle_status = {}

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
            DATA = rm_symbol(data_string[2:-2])
            if ((BEETLE_ID == self.ID) and (PACKET_ID == '0') and (DATA == "ACK")):
                connection_threads[self.connection_index].ACK=True
            if ((BEETLE_ID == self.ID) and (PACKET_ID == '1') and (DATA == "HANDSHAKE")): 
                connection_threads[self.connection_index].handshake=True
            if ((BEETLE_ID == self.ID) and (PACKET_ID == '2') and (DATA == "GUN")): 
                connection_threads[self.connection_index].handshake=True
            if ((BEETLE_ID == self.ID) and (PACKET_ID == '3') and (DATA == "VEST")): 
                connection_threads[self.connection_index].handshake=True
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
        else:
            print("ERR in CRC")
            time.sleep(0.01)


#Thread generation for each beetle
class ConnectionHandlerThread(Thread):
    recent_time = time.time()
    handshake = False
    ACK = False
    clear =False
    sync =False
    last_sync_time=0
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
        self.handshake_proto(self.connection)
        while True:
            if (self.reconnect):
                time.sleep(1)
                print("reconnect")
                self.clear_proto(self.connection)
            try:
                if (self.connection_index==0):
                    #call data collecting comms
                    self.data_proto(self.connection)
                else:
                    #call position collectiog comms
                    self.pos_proto(self.connection)
            except BTLEException:
                #will only enter if problem with connection. IE disconnect
                self.connection.disconnect()
                #start a function to create new thread
                reconnect = Thread(target=reconnection(self.addr,self.connection_index))
                reconnect.start()
                #Current Thread END
                sys.exit(1)

    def clear_proto(self,p):
        while not self.handshake:
            self.characteristic.write(bytes("H", "utf-8"), withResponse=False)
            # Wait for Handshake packet from bluno 
            p.waitForNotifications(0.01)
        self.handshake=False

    def handshake_proto(self,p):
        # Send handshake packet
        print("HANDSHAKE INITIATED")
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

    def pos_proto(self,p):
        while True:
            p.waitForNotifications(1)
            
    def data_proto(self,p):
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
        t = ConnectionHandlerThread(i, beetle_addresses[i], False)
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
                t = ConnectionHandlerThread(index, addr, True)
                #start thread
                t.start()
                connection_threads[index]=t
                break
            except Exception:
                time.sleep(1)
                continue

#data processing for incoming packets
def clean_data(info):
    return(info[2:-1])

#data processing for incoming packets
def rm_symbol(data):
    while True:
        if (data[0] == '#'):
            data = data[1:]
        else:
            return data

#Fucntion to check CRC match data receive
def crc_check(data_string):
    hash = crc8.crc8()
    crc = data_string[-2:]
    data_string = data_string[2:-2]
    hash.update(bytes(data_string, "utf-8"))
    if (hash.hexdigest() == crc):
        return True
    else:
        return False

def main():
    establish_connection()

if __name__ == "__main__":
    main()