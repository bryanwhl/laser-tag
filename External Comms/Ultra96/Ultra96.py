from socket import *
from threading import Thread, Timer
from base64 import b64encode, b64decode
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import json
from pygments import highlight, lexers, formatters
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
THRESHOLD = 10000 # Tune this value

# Gamemode - 1P/2P/2P Unrestricted (1/2/3)
GAMEMODE = int(sys.argv[1])
# Check if valid GAMEMODE
if GAMEMODE not in (1, 2, 3):
    print("Invalid gamemode! 1 - 1P | 2 - 2P | 3 - 2P Unrestricted")
    exit()

# Init Queues
gun_one_queue = []
gun_two_queue = []
vest_one_queue = []
vest_two_queue = []
motion_one_queue = []
motion_two_queue = []
action_one_queue = []
action_two_queue = []

message_queue = []

# Init game state
initial_game_state = {
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
        while True:
            try:
                self.HOST = HOST
                self.PORT = PORT
                self.serverSocket = socket(AF_INET, SOCK_STREAM)
                self.serverSocket.bind((HOST,PORT))
                self.client_sockets = []
                break
            except BrokenPipeError:
                sleep(0.1)

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
                vest_one_queue.append(1) if x[1] == '0' else vest_two_queue.append(1)
            elif(x[0] == "gun"):
                gun_one_queue.append(1) if x[1] == '0' else  gun_two_queue.append(1) 
            else:
                unpacked = eval(x[1])
                motion_one_queue.append(unpacked) if x[0] == '1' else motion_two_queue.append(unpacked)
            
            

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
                serverThread = Thread(target=self.thread_DataServer_Receiver, args=(connSocket, clientAddr))
                serverThread.start()
        except KeyboardInterrupt:
            print("Closing socket")
            self.serverSocket.close()

class EvalClient:
    def __init__(self, HOST, PORT):
        while True:
            try:
                self.HOST = HOST
                self.PORT = PORT
                self.clientSocket = socket(AF_INET, SOCK_STREAM)
                self.clientSocket.connect((HOST, PORT))
                break
            except BrokenPipeError:
                sleep(0.1)

    # Eval Client Thread
    def thread_EvalClient(self):
        try:
            while True:
                # Check if message_queue has any messages
                while message_queue:
                    message = json.dumps(message_queue.pop())
                    encodedMessage = message.encode()
                    # Encrypt data
                    cipher = AES.new(key, AES.MODE_CBC)
                    encryptedMessage = cipher.iv + cipher.encrypt(pad(encodedMessage, AES.block_size))
                    encryptedMessage_64 = b64encode(encryptedMessage)
                    len_byte = str(len(encryptedMessage_64)).encode("utf-8") + b'_'
                    finalmsg = len_byte+encryptedMessage_64
                    # Send data
                    self.clientSocket.send(finalmsg)
                    # Pop from message_queue
                    message_queue.clear()

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
                    ge.game_state = updated_game_state
                    # Send updated HP and Bullets to Relay - [HP1, HP2, Bullet1, Bullet2]
                    hp_and_bullet = str([updated_game_state["p1"]["hp"], updated_game_state["p2"]["hp"], updated_game_state["p1"]["bullets"], updated_game_state["p2"]["bullets"]])
                    ds.send_to_relay(hp_and_bullet)
                    
                    
        except KeyboardInterrupt:
            print("Closing Client Socket")
            self.clientSocket.close()  

class GameEngine:
    def __init__(self):
        self.game_state = initial_game_state
        self.shieldEndTimes = {1: datetime.datetime.now() , 2: datetime.datetime.now()}
        
    def shoot_bullet(self, player):
        if player == 1:
            self.game_state["p1"]["bullets"] -= 1 if self.game_state["p1"]["bullets"] > 0 else 0
        else:
            self.game_state["p2"]["bullets"] -= 1 if self.game_state["p2"]["bullets"] > 0 else 0

    def take_damage(self, player, damage):
        overflow_damage = damage - self.game_state["p1"]["shield_health"] if player == 1 else damage - self.game_state["p2"]["shield_health"]
        if player == 1:
            if overflow_damage > 0:
                self.game_state["p1"]["hp"] -= overflow_damage
                self.game_state["p1"]["shield_health"] = 0
            else:
                self.game_state["p1"]["shield_health"] -= damage
        else:
            if overflow_damage > 0:
                self.game_state["p2"]["hp"] -= overflow_damage
                self.game_state["p2"]["shield_health"] = 0
            else:
                self.game_state["p2"]["shield_health"] -= damage

    def get_hit(self, player):
        if player == 1:
            if self.game_state["p2"]["bullets"] > 0:
                self.take_damage(1, 10) 
        else:
            if self.game_state["p1"]["bullets"] > 0:
                self.take_damage(2, 10)

    def throw_grenade(self, player):
        if player == 1:
            if self.game_state["p1"]["grenades"] > 0:
                self.take_damage(2, 30)
                self.game_state["p1"]["grenades"] -= 1
        else:
            if self.game_state["p2"]["grenades"] > 0:
                self.take_damage(1, 30)
                self.game_state["p2"]["grenades"] -= 1

    def reload_gun(self, player):
        if player == 1:
            self.game_state["p1"]["bullets"] = 6 if self.game_state["p1"]["bullets"] == 0 else self.game_state["p1"]["bullets"]
        else:
            self.game_state["p2"]["bullets"] = 6 if self.game_state["p2"]["bullets"] == 0 else self.game_state["p2"]["bullets"]

    def activate_shield(self, player):
        if player == 1:
            if self.game_state["p1"]["num_shield"] > 0 and self.game_state["p1"]["shield_time"] == 0:
                self.game_state["p1"]["shield_health"] = 30
                self.game_state["p1"]["shield_time"] = 10
                self.game_state["p1"]["num_shield"] -= 1
                shieldTimer = Timer(10, self.shield_timeout, args=(1,))
                shieldTimer.start()
                self.shieldEndTimes[1] = datetime.datetime.now() + datetime.timedelta(seconds=10)
        else:
            if self.game_state["p2"]["num_shield"] > 0 and self.game_state["p2"]["shield_time"] == 0:
                self.game_state["p2"]["shield_health"] = 30
                self.game_state["p2"]["shield_time"] = 10
                self.game_state["p2"]["num_shield"] -= 1
                shieldTimer = Timer(10, self.shield_timeout, args=(2,))
                shieldTimer.start()
                self.shieldEndTimes[2] = datetime.datetime.now() + datetime.timedelta(seconds=10)

    def respawn_player_if_dead(self):
        if self.game_state["p1"]["hp"] <= 0:
            print("Player 1 Respawned")
            curr_num_deaths = self.game_state["p1"]["num_deaths"]
            self.game_state["p1"] = {
                            "hp": 100,
                            "action": "",
                            "bullets": 6,
                            "grenades": 2,
                            "shield_time": 0,
                            "shield_health": 0,
                            "num_deaths": curr_num_deaths + 1,
                            "num_shield": 3
                        }
        if self.game_state["p2"]["hp"] <= 0:
            print("Player 2 Respawned")
            curr_num_deaths = self.game_state["p2"]["num_deaths"]
            self.game_state["p2"] = {
                            "hp": 100,
                            "action": "",
                            "bullets": 6,
                            "grenades": 2,
                            "shield_time": 0,
                            "shield_health": 0,
                            "num_deaths": curr_num_deaths + 1,
                            "num_shield": 3
                        }

    def shield_timeout(self, player):
        print("P", str(player), "Shield Timeout")
        if player == 1:
            self.game_state["p1"]["shield_health"] = 0
        else:
            self.game_state["p2"]["shield_health"] = 0

    def update_shield_timers(self):
        if self.shieldEndTimes[1] > datetime.datetime.now():
            timeLeft = self.shieldEndTimes[1] - datetime.datetime.now()
            timeLeft = int(timeLeft.total_seconds())
            self.game_state["p1"]["shield_time"] = timeLeft
        if self.shieldEndTimes[2] > datetime.datetime.now():
            timeLeft = self.shieldEndTimes[2] - datetime.datetime.now()
            timeLeft = int(timeLeft.total_seconds())
            self.game_state["p2"]["shield_time"] = timeLeft

    def handle_player_action(self, player):
        action = action_one_queue.pop() if player == 1 else action_two_queue.pop()
        if action == "grenade":
            self.update_game_state(player, "grenade")
        elif action == "shield":
            self.update_game_state(player, "shield")
        elif action == "reload":
            self.update_game_state(player, "reload")
        elif action == "logout":
            self.update_game_state(player, "logout")
        
    def update_game_state(self, player, action):
        print("P", str(player), " - ", action)
        # Shoot if player has bullets
        if action == "shoot":
            self.shoot_bullet(player)
        # Player loses 10 HP from getting hit
        elif action == "hit":
            self.get_hit(player)
        # Opponent always gets hit by grenade
        elif action == "grenade":
            self.throw_grenade(player)
        # Reload only if player has 0 bullets
        elif action == "reload":
            self.reload_gun(player)
        # Give player a shield 
        elif action == "shield":
            self.activate_shield(player)
        elif action == "shield_timeout":
            self.shield_timeout(player)
        elif action == "logout":
            # Add logout
            pass

        # Respawns player if dead
        self.respawn_player_if_dead()

        # Update players' shield timers
        self.update_shield_timers()

    # Game Engine Thread
    def thread_GameEngine(self):
        # ONE PLAYER GAME ENGINE
        # Checks for player 1's action + player 2's vest
        if GAMEMODE == 1:  
            while True:
                # Waits for player 1 action
                while not gun_one_queue and not action_one_queue:
                    pass

                # ADD SLEEP TO WAIT FOR VEST TO GET HIT??
                sleep(0.5)

                # Check for P2 vest
                if vest_two_queue:
                    self.update_game_state(2, "hit")

                # Check for P1 actions
                if gun_one_queue:
                    self.update_game_state(1, "shoot")
                elif action_one_queue:
                    self.handle_player_action(1)

                # Clear all action buffers
                gun_one_queue.clear()
                action_one_queue.clear()
                vest_two_queue.clear()

                # Add to message_queue to send to eval server
                message_queue.append(self.game_state)
                
                # Print out for debugging purposes
                formatted_json = json.dumps(self.game_state, indent=4)
                pretty_json = highlight(formatted_json, lexers.JsonLexer(), formatters.TerminalFormatter())
                print(pretty_json, '\n')
                

        # TWO PLAYER GAME ENGINE
        # Checks for both player 1 and 2 action and vest
        elif GAMEMODE == 2:
            while True:
                # Waits for player 1 and 2 action
                while (not gun_one_queue and not action_one_queue) or (not gun_two_queue and not action_two_queue):
                    pass
                
                # ADD SLEEP TO WAIT FOR VEST TO GET HIT??
                sleep(0.5)

                # Check for P1 vest
                if vest_one_queue:
                    self.update_game_state(1, "hit")

                # Check for P2 vest
                if vest_two_queue:
                    self.update_game_state(2, "hit")

                # Check for P1 actions
                if gun_one_queue:
                    self.update_game_state(1, "shoot")
                elif action_one_queue:
                    self.handle_player_action(1)
                
                # Check for P2 actions
                if gun_two_queue:
                    self.update_game_state(2, "shoot")
                elif action_two_queue:
                    self.handle_player_action(2)

                # Clear all action buffers
                gun_one_queue.clear()
                gun_two_queue.clear()
                action_one_queue.clear()
                action_two_queue.clear()
                vest_one_queue.clear()
                vest_two_queue.clear()

                # Add to message_queue to send to eval server
                message_queue.append(self.game_state)

                # Print out for debugging purposes
                formatted_json = json.dumps(self.game_state, indent=4)
                pretty_json = highlight(formatted_json, lexers.JsonLexer(), formatters.TerminalFormatter())
                print(pretty_json, '\n')
        
        # TWO PLAYER UNRESTRICTED GAME ENGINE
        elif GAMEMODE == 3:
            while True:
                # TO IMPLEMENT
                pass

class HardwareAI:

    def __init__(self):
        self.queue = []

    def append_10_readings_to_queue(self, readings): # readings: 2D list of 10 readings * 6 attributes
        for reading in readings:
            self.queue.append(reading)
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

        difference = 0
        for i in range(6):
            difference += abs(sum_of_first_10_readings[i] - sum_of_next_10_readings[i])

        return difference > THRESHOLD

    def predict(self):
      
        if len(self.queue) < 20:
            print("function submit_input: input length is less than 20")
            return []

        random_classification = random.randint(0, 4)
        return INT_TO_ACTION_MAPPING[random_classification]

    def thread_hardware_ai_p1(self):
        global motion_one_queue
        while True:
            # Append to buffer if motion queue exceeds 10 readings
            if len(motion_one_queue) >= 10:
                self.append_10_readings_to_queue(motion_one_queue[-10:])
                motion_one_queue = motion_one_queue[:-10]

            # Classify action if current buffer detects start of move
            if self.detect_start_of_move():
                action_classified = self.predict()
                if action_classified != "nil":
                    action_one_queue.append(action_classified)
                    
    def thread_hardware_ai_p2(self):
        global motion_two_queue
        while True:
            # Append to buffer if motion queue exceeds 10 readings
            if len(motion_two_queue) >= 10:
                self.append_10_readings_to_queue(motion_two_queue[-10:])
                motion_two_queue = motion_two_queue[:-10]

            # Classify action if current buffer detects start of move
            if self.detect_start_of_move():
                action_classified = self.predict()
                if action_classified != "nil":
                    action_two_queue.append(action_classified)

def thread_debug():
    while True:
        # print("GUN 1 - ", gun_one_queue)
        # print("GUN 2 - ", gun_two_queue):ue)

        # print("Motion size = ", len(motion_one_queue))
        print(action_one_queue)

def thread_mockP1():
    while True:
        action_one_queue.append('grenade')
        sleep(2)
        gun_one_queue.append(1)
        sleep(2)
        gun_one_queue.append(1)
        sleep(2)
        gun_one_queue.append(1)
        sleep(2)
        gun_one_queue.append(1)
        sleep(2)
        gun_one_queue.append(1)
        sleep(2)
        action_one_queue.append('grenade')
        break

def thread_mockP2():
    while True:
        action_two_queue.append('reload')
        sleep(2)
        action_two_queue.append('reload')
        vest_two_queue.append(1)
        sleep(2)
        action_two_queue.append('reload')
        vest_two_queue.append(1)
        sleep(2)
        action_two_queue.append('reload')
        vest_two_queue.append(1)
        sleep(2)
        action_two_queue.append('reload')
        vest_two_queue.append(1)
        sleep(2)
        action_two_queue.append('reload')
        vest_two_queue.append(1)
        sleep(2)
        action_two_queue.append('reload')
        break

# Init global objects
ds = DataServer(DATA_HOST, DATA_PORT)
# ec = EvalClient(EVAL_HOST, EVAL_PORT)
ge = GameEngine()
ai1 = HardwareAI()
ai2 = HardwareAI()

def main():
    print("GAMEMODE-", GAMEMODE)

    data_server_thread = Thread(target=ds.thread_DataServer)
    # eval_server_thread = Thread(target=ec.thread_EvalClient)
    game_engine_thread = Thread(target=ge.thread_GameEngine)
    hardware_ai_p1_thread = Thread(target=ai1.thread_hardware_ai_p1)
    hardware_ai_p2_thread = Thread(target=ai1.thread_hardware_ai_p2)
    mock_test_p1_thread = Thread(target=thread_mockP1)
    mock_test_p2_thread = Thread(target=thread_mockP2)

    # debug_thread = Thread(target=thread_debug)


    # eval_server_thread.start()
    game_engine_thread.start()
    hardware_ai_p1_thread.start()
    hardware_ai_p2_thread.start()
    mock_test_p1_thread.start()
    mock_test_p2_thread.start()
    # debug_thread.start()
    


if __name__ == "__main__":
    main()
