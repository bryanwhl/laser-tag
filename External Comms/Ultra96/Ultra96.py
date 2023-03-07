from socket import *
import threading as t
from base64 import b64encode, b64decode
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import json
import random
import datetime
from time import sleep
import sys

# Init connection settings
DATA_HOST = gethostname()
DATA_PORT = 8080

EVAL_HOST = "192.168.95.247"
EVAL_PORT = 1515

# Variables for Hardware AI
WINDOW_SIZE = 20
INT_TO_ACTION_MAPPING = {
    0: 'grenade',
    1: 'shield',
    2: 'reload',
    3: 'logout',
    4: 'nil'
}
THRESHOLD = 100 # Tune this value

# Gamemode - 1P/2P/2P Unrestricted (1/2/3)
GAMEMODE = int(sys.argv[1])
# Check if valid GAMEMODE
if GAMEMODE not in (1, 2, 3):
    print("Invalid gamemode! 1 - 1P | 2 - 2P | 3 - 2P Unrestricted")
    exit()

# Init Queues
gunOneQueue = []
gunTwoQueue = []
vestOneQueue = []
vestTwoQueue = []
motionOneQueue = []
motionTwoQueue = []
actionOneQueue = []
actionTwoQueue = []

messageQueue = []

# Init game state
initGameState = {
                        "p1": {
                            "hp": 100,
                            "action": "",
                            "bullets": 6,
                            "grenades": 2,
                            "shield_time": 0,
                            "shield_health": 0,
                            "num_deaths": 0,
                            "num_shield": 3
                        },
                        "p2": {
                            "hp": 100,
                            "action": "",
                            "bullets": 6,
                            "grenades": 2,
                            "shield_time": 0,
                            "shield_health": 0,
                            "num_deaths": 0,
                            "num_shield": 3
                        }
                    }

# Init Encryption settings
key = "thisismysecretky"
key = bytes(str(key), encoding="utf8")

actions = ['shoot', 'hit', 'grenade', 'reload', 'shield', 'logout', 'shield_timeout']

class DataServer:
    def __init__(self, HOST, PORT):
        self.HOST = HOST
        self.PORT = PORT
        self.serverSocket = socket(AF_INET, SOCK_STREAM)
        self.serverSocket.bind((HOST,PORT))
        self.client_sockets = []

    def send_to_relay(self, message):
        encodedMessage = message.encode()
        # Encrypt data
        cipher = AES.new(key, AES.MODE_CBC)
        encryptedMessage = cipher.iv + cipher.encrypt(pad(encodedMessage, AES.block_size))
        encryptedMessage_64 = b64encode(encryptedMessage)
        len_byte = str(len(encryptedMessage_64)).encode("utf-8") + b'_'
        finalmsg = len_byte+encryptedMessage_64

        # Send to all clients
        for client_socket in self.client_sockets:
            client_socket.send(finalmsg)

    # Thread to receive the message
    def thread_DataServer_Receiver(self,connSocket, clientAddr):
        while True:
            # Receive and Parse message (len_EncryptedMessage)
            # recv length followed by '_' followed by cypher
            message = b''
            while not message.endswith(b'_'):
                _d = connSocket.recv(1)
                if not _d:
                    message = b''
                    break
                message += _d
            if len(message) == 0:
                print('no more data from the client')
                self.serverSocket.close()
                return

            message = message.decode("utf-8")
            length = int(message[:-1])
            message = b''
            while len(message) < length:
                _d = connSocket.recv(length - len(message))
                if not _d:
                    message = b''
                    break
                message += _d
            if len(message) == 0:
                print('no more data from the client')
                self.serverSocket.close()
                return
            decodedMessage = b64decode(message)

            iv = decodedMessage[:AES.block_size]
            cipher = AES.new(key, AES.MODE_CBC, iv)
            decryptedMessage = cipher.decrypt(decodedMessage[16:])
            decryptedMessage = unpad(decryptedMessage, AES.block_size)
            decryptedMessage = decryptedMessage.decode()
            x = decryptedMessage.split()
            if(x[0] == "vest"):
                vestOneQueue.append(1) if x[1] == '0' else vestTwoQueue.append(1)
            elif(x[0] == "gun"):
                gunOneQueue.append(1) if x[1] == '0' else  gunTwoQueue.append(1) 
            else:
                unpacked = eval(decryptedMessage)
                motionOneQueue.append(unpacked) if unpacked["id"] == '1' else motionTwoQueue.append(unpacked)
            
            

    # Data Server Thread
    def thread_DataServer(self):
        # Listens for incoming connections
        self.serverSocket.listen()
        print("Data Server is ready to receive message")

        try:
            while True:
                # Upon successful connection with a client socket, spawns a new thead
                connSocket, clientAddr = self.serverSocket.accept()
                self.client_sockets.append(connSocket)
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
                    message = json.dumps(messageQueue.pop())
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
                    messageQueue.clear()

                    # Receive updated game state (Ground Truth)
                    message = b''
                    while not message.endswith(b'_'):
                        _d = self.clientSocket.recv(1)
                        if not _d:
                            message = b''
                            break
                        message += _d
                    if len(message) == 0:
                        print('no more data from the client')
                        self.serverSocket.close()
                        return

                    message = message.decode("utf-8")
                    length = int(message[:-1])
                    message = b''
                    while len(message) < length:
                        _d = self.clientSocket.recv(length - len(message))
                        if not _d:
                            message = b''
                            break
                        message += _d
                    if len(message) == 0:
                        print('no more data from the client')
                        self.clientSocket.close()
                        return
                    decodedMessage = message.decode()
                    # Update game state to ground truth
                    updated_game_state = json.loads(decodedMessage)
                    ge.gameState = updated_game_state
                    # Send updated HP and Bullets to Relay - [HP1, HP2, Bullet1, Bullet2]
                    hp_and_bullet = str([updated_game_state["p1"]["hp"], updated_game_state["p2"]["hp"], updated_game_state["p1"]["bullets"], updated_game_state["p2"]["bullets"]])
                    ds.send_to_relay(hp_and_bullet)
                    
                    
        except KeyboardInterrupt:
            print("Closing Client Socket")
            self.clientSocket.close()  

class GameEngine:
    def __init__(self):
        self.gameState = initGameState
        self.shieldEndTimes = {1: datetime.datetime.now() , 2: datetime.datetime.now()}
        
    def shootBullet(self, player):
        if player == 1:
            self.gameState["p1"]["bullets"] -= 1 if self.gameState["p1"]["bullets"] > 0 else 0
        else:
            self.gameState["p2"]["bullets"] -= 1 if self.gameState["p2"]["bullets"] > 0 else 0

    def getHit(self, player):
        if player == 1:
            self.gameState["p1"]["hp"] -= 10 if self.gameState["p2"]["bullets"] > 0 else 0
        else:
            self.gameState["p2"]["hp"] -= 10 if self.gameState["p1"]["bullets"] > 0 else 0

    def throwGrenade(self, player):
        if player == 1:
            self.gameState["p2"]["hp"] -= 30
        else:
            self.gameState["p1"]["hp"] -= 30

    def reloadGun(self, player):
        if player == 1:
            self.gameState["p1"]["bullets"] = 6 if self.gameState["p1"]["bullets"] == 0 else self.gameState["p1"]["bullets"]
        else:
            self.gameState["p2"]["bullets"] = 6 if self.gameState["p2"]["bullets"] == 0 else self.gameState["p2"]["bullets"]

    def activateShield(self, player):
        if player == 1:
            if self.gameState["p1"]["num_shield"] > 0 and self.gameState["p1"]["shield_time"] == 0:
                self.gameState["p1"]["shield_health"] = 30
                self.gameState["p1"]["shield_time"] = 10
                shieldTimer = t.Timer(10, self.shieldTimeout, args=1)
                shieldTimer.start()
                self.shieldEndTimes[1] = datetime.datetime.now() + datetime.timedelta(seconds=10)
        else:
            if self.gameState["p2"]["num_shield"] > 0 and self.gameState["p2"]["shield_time"] == 0:
                self.gameState["p2"]["shield_health"] = 30
                self.gameState["p2"]["shield_time"] = 10
                shieldTimer = t.Timer(10, self.shieldTimeout, args=2)
                shieldTimer.start()
                self.shieldEndTimes[2] = datetime.datetime.now() + datetime.timedelta(seconds=10)

    def respawnPlayersIfDead(self):
        if self.gameState["p1"]["hp"] <= 0:
            self.gameState["p1"] = {
                            "hp": 100,
                            "action": "",
                            "bullets": 6,
                            "grenades": 2,
                            "shield_time": 0,
                            "shield_health": 0,
                            "num_deaths": 0,
                            "num_shield": 3
                        }
        if self.gameState["p2"]["hp"] <= 0:
            self.gameState["p2"] = {
                            "hp": 100,
                            "action": "",
                            "bullets": 6,
                            "grenades": 2,
                            "shield_time": 0,
                            "shield_health": 0,
                            "num_deaths": 0,
                            "num_shield": 3
                        }

    def shieldTimeout(self, player):
        if player == 1:
            self.gameState["p1"]["shield_health"] = 0
        else:
            self.gameState["p2"]["shield_health"] = 0

    def updateShieldTimers(self):
        if self.shieldEndTimes[1] > datetime.datetime.now():
            timeLeft = self.shieldEndTimes[1] - datetime.datetime.now()
            timeLeft = int(timeLeft.timedelta.total_seconds())
            self.gameState["p1"]["shield_time"] = timeLeft
        if self.shieldEndTimes[2] > datetime.datetime.now():
            timeLeft = self.shieldEndTimes[2] - datetime.datetime.now()
            timeLeft = int(timeLeft.timedelta.total_seconds())
            self.gameState["p2"]["shield_time"] = timeLeft

    def updateGameState(self, player, action):
        # Shoot if player has bullets
        if action == "shoot":
            self.shootBullet(player)
        # Player loses 10 HP from getting hit
        elif action == "hit":
            self.getHit(player)
        # Opponent always gets hit by grenade
        elif action == "grenade":
            self.throwGrenade(player)
        # Reload only if player has 0 bullets
        elif action == "reload":
            self.reloadGun(player)
        # Give player a shield 
        elif action == "shield":
            self.activateShield(player)
        elif action == "shield_timeout":
            self.shieldTimeout(player)

        # Respawns player if dead
        self.respawnPlayersIfDead()

        # Update players' shield timers
        self.updateShieldTimers()

    # Game Engine Thread
    def thread_GameEngine(self):
        # ONE PLAYER GAME ENGINE
        # Checks for player 1's action + player 2's vest
        if GAMEMODE == 1:  
            while True:
                # Waits for player 1 action
                while not gunOneQueue and not actionOneQueue:
                    pass

                # ADD SLEEP TO WAIT FOR VEST TO GET HIT??
                sleep(0.5)

                # Check for P2 vest
                if vestTwoQueue:
                    self.updateGameState(2, "hit")

                # Check for P1 actions
                if gunOneQueue:
                    self.updateGameState(1, "shoot")
                elif actionOneQueue:
                    # TO ADD IMPLEMENTATION WITH BRYAN
                    pass

                # Clear all action buffers
                gunOneQueue.clear()
                actionOneQueue.clear()
                vestTwoQueue.clear()

                # Add to messageQueue to send to eval server
                messageQueue.append(self.gameState)
                

        # TWO PLAYER GAME ENGINE
        # Checks for both player 1 and 2 action and vest
        elif GAMEMODE == 2:
            while True:
                # Waits for player 1 and 2 action
                while (not gunOneQueue and not actionOneQueue) or (not gunTwoQueue and not actionTwoQueue):
                    pass
                
                # ADD SLEEP TO WAIT FOR VEST TO GET HIT??
                sleep(0.5)

                # Check for P1 vest
                if vestOneQueue:
                    self.updateGameState(1, "hit")

                # Check for P2 vest
                if vestTwoQueue:
                    self.updateGameState(2, "hit")

                # Check for P1 actions
                if gunOneQueue:
                    self.updateGameState(1, "shoot")
                elif actionOneQueue:
                    # TO ADD IMPLEMENTATION WITH BRYAN
                    pass
                
                # Check for P2 actions
                if gunTwoQueue:
                    self.updateGameState(2, "shoot")
                elif actionTwoQueue:
                    # TO ADD IMPLEMENTATION WITH BRYAN
                    pass

                # Clear all action buffers
                gunOneQueue.clear()
                gunTwoQueue.clear()
                actionOneQueue.clear()
                actionTwoQueue.clear()
                vestOneQueue.clear()
                vestTwoQueue.clear()

                # Add to messageQueue to send to eval server
                messageQueue.append(self.gameState)
        
        # TWO PLAYER UNRESTRICTED GAME ENGINE
        elif GAMEMODE == 3:
            while True:
                # TO IMPLEMENT
                pass

class HardwareAI:

    def __init__(self):
        self.queue = []

    def append_10_readings_to_queue(self, readings): # readings: 2D list of 10 readings * 6 attributes
        self.queue.append(readings)
        if len(self.queue) >= 30:
            self.queue = self.queue[10:]

    def detect_start_of_move(self): # 2D array of 20 * 6 dimensions
        if len(self.queue) < 20:
            return ''
        move_list = self.queue[:20]
        sum_of_first_10_readings = [0, 0, 0, 0, 0, 0]
        sum_of_next_10_readings = [0, 0, 0, 0, 0, 0]
        for attribute_idx in range(6):
            for reading_no in range(10):
                sum_of_first_10_readings[attribute_idx] += move_list[reading_no][attribute_idx]
            for reading_no in range(10, 20):
                sum_of_next_10_readings[attribute_idx] += move_list[reading_no][attribute_idx]
        difference = sum(sum_of_next_10_readings) - sum(sum_of_first_10_readings)
        return difference > THRESHOLD

    def predict(self):
      
        if len(self.queue) < 20:
            print("function submit_input: input length is less than 20")
            return []

        random_classification = random.randint(0, 5)
        return INT_TO_ACTION_MAPPING[random_classification]

    def thread_hardware_ai(self):
        while True:
            if len(motionOneQueue) >= 10:
                self.get_action(motionOneQueue[-10:])
                motionOneQueue = motionOneQueue[:-10]

def thread_debug():
    while True:
        print("GUN 1 - ", gunOneQueue)
        print("GUN 2 - ", gunTwoQueue)
        print("VEST 1 - ", vestOneQueue)
        print("VEST 2 - ", vestTwoQueue)
        print("MOTION 1 - ", motionOneQueue)
        print("MOTION 2 - ", motionTwoQueue)

# Init global objects
ds = DataServer(DATA_HOST, DATA_PORT)
ec = EvalClient(EVAL_HOST, EVAL_PORT)
ge = GameEngine()

def main():
    print("GAMEMODE-", GAMEMODE)

    dataServerThread = t.Thread(target=ds.thread_DataServer)
    evalServerThread = t.Thread(target=ec.thread_EvalClient)
    gameEngineThread = t.Thread(target=ge.thread_GameEngine)


    # debugThread = t.Thread(target=thread_debug)

    dataServerThread.start()
    evalServerThread.start()
    gameEngineThread.start()
    # debugThread.start()
    


if __name__ == "__main__":
    main()
