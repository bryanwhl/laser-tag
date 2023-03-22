from socket import *
from threading import Thread, Timer
from base64 import b64encode, b64decode
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import json
from pygments import highlight, lexers, formatters
import datetime
from time import sleep
import sys
import os
from pynq import Overlay

import pynq.lib.dma
from pynq import DefaultIP
from pynq import allocate
import numpy as np
from struct import unpack, pack
import time
from math import exp

# Init connection settings
DATA_HOST = gethostname()
DATA_PORT1 = 8080
DATA_PORT2 = 7070

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

global action_flag_1
global action_flag_2
global last_action_time_1
global last_action_time_2

action_flag_1 = True
action_flag_2 = True
last_action_time_1 = datetime.datetime.now()
last_action_time_2 = datetime.datetime.now()

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
    global action_flag_1
    global action_flag_2
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
        global action_flag_1
        global action_flag_2
        global last_action_time_1
        global last_action_time_2
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
                if x[0] == '0':
                    motion_one_queue.append(unpacked)
                    action_flag_1 = False
                    last_action_time_1 = datetime.datetime.now()
                    
                else:
                    motion_two_queue.append(unpacked)
                    action_flag_2 = False
                    last_action_time_2 = datetime.datetime.now()
            

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
                    # Check for either player logout
                    if updated_game_state["p1"]["action"] == "logout":
                        ge.reset_player(1)
                    if updated_game_state["p2"]["action"] == "logout":
                        ge.reset_player(2)
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
        self.p1_move = False
        self.p2_move = False
        self.is_game_over = False
        
    def shoot_bullet(self, player):
        if player == 1:
            self.game_state["p1"]["bullets"] -= 1 if self.game_state["p1"]["bullets"] > 0 else 0
            self.game_state["p1"]["action"] = "shoot"
        else:
            self.game_state["p2"]["bullets"] -= 1 if self.game_state["p2"]["bullets"] > 0 else 0
            self.game_state["p2"]["action"] = "shoot"

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
                self.game_state["p1"]["action"] = "grenade"
        else:
            if self.game_state["p2"]["grenades"] > 0:
                self.take_damage(1, 30)
                self.game_state["p2"]["grenades"] -= 1
                self.game_state["p2"]["action"] = "grenade"

    def reload_gun(self, player):
        if player == 1:
            self.game_state["p1"]["bullets"] = 6 if self.game_state["p1"]["bullets"] == 0 else self.game_state["p1"]["bullets"]
            self.game_state["p1"]["action"] = "reload"
        else:
            self.game_state["p2"]["bullets"] = 6 if self.game_state["p2"]["bullets"] == 0 else self.game_state["p2"]["bullets"]
            self.game_state["p2"]["action"] = "reload"

    def activate_shield(self, player):
        if player == 1:
            if self.game_state["p1"]["num_shield"] > 0 and self.game_state["p1"]["shield_time"] == 0:
                self.game_state["p1"]["shield_health"] = 30
                self.game_state["p1"]["shield_time"] = 10
                self.game_state["p1"]["num_shield"] -= 1
                self.game_state["p1"]["action"] = "shield"
                shieldTimer = Timer(10, self.shield_timeout, args=(1,))
                shieldTimer.start()
                self.shieldEndTimes[1] = datetime.datetime.now() + datetime.timedelta(seconds=10)
        else:
            if self.game_state["p2"]["num_shield"] > 0 and self.game_state["p2"]["shield_time"] == 0:
                self.game_state["p2"]["shield_health"] = 30
                self.game_state["p2"]["shield_time"] = 10
                self.game_state["p2"]["num_shield"] -= 1
                self.game_state["p2"]["action"] = "shield"
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

    def reset_player(self, player):
        if player == 1:
            self.game_state["p1"]["hp"] = 100
            self.game_state["p1"]["action"] = ""
            self.game_state["p1"]["bullets"] = 6
            self.game_state["p1"]["grenades"] = 2
            self.game_state["p1"]["shield_time"] = 0
            self.game_state["p1"]["shield_health"] = 0
            self.game_state["p1"]["num_deaths"] = 0
            self.game_state["p1"]["num_shield"] = 3
        if player == 2:
            self.game_state["p2"]["hp"] = 100
            self.game_state["p2"]["action"] = ""
            self.game_state["p2"]["bullets"] = 6
            self.game_state["p2"]["grenades"] = 2
            self.game_state["p2"]["shield_time"] = 0
            self.game_state["p2"]["shield_health"] = 0
            self.game_state["p2"]["num_deaths"] = 0
            self.game_state["p2"]["num_shield"] = 3

    def logout(self, player):
        if player == 1:
            self.game_state["p1"]["action"] = "logout"
        if player == 2:
            self.game_state["p2"]["action"] = "logout"

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
            self.logout()

        # Respawns player if dead
        self.respawn_player_if_dead()

        # Update players' shield timers
        self.update_shield_timers()

    # Game Engine Thread
    def thread_GameEngine(self):
        # Starts game upon input
        print("Press 'Enter' when game starts...")
        input()

        # Flush any inital data
        motion_one_queue.clear()
        motion_two_queue.clear()
        gun_one_queue.clear()
        gun_two_queue.clear()
        vest_one_queue.clear()
        vest_two_queue.clear()
        motion_one_queue.clear()
        motion_two_queue.clear()
        action_one_queue.clear()
        action_two_queue.clear()

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
                
                # Check for shield and prioritise action
                if action_one_queue:
                    if action_one_queue[0] == 'shield':
                        self.handle_player_action(1)
                        self.p1_move = True
                if action_two_queue:
                    if action_two_queue[0] == 'shield':
                        self.handle_player_action(2)
                        self.p2_move = True

                # ADD SLEEP TO WAIT FOR VEST TO GET HIT??
                sleep(0.5)

                # Check for P1 vest
                if vest_one_queue:
                    self.update_game_state(1, "hit")

                # Check for P2 vest
                if vest_two_queue:
                    self.update_game_state(2, "hit")

                # Check for P1 actions if not shield
                if not self.p1_move:
                    if gun_one_queue:
                        self.update_game_state(1, "shoot")
                    elif action_one_queue:
                        self.handle_player_action(1)
                
                # Check for P2 actions if not shield
                if not self.p2_move:
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

                # Reset moves checks
                self.p1_move = False
                self.p2_move = False

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

    def __init__(self, player):
        self.player = player
        self.overlay = Overlay('/home/xilinx/new_data_bitstream.bit')
        self.dma = self.overlay.axi_dma_0

    def predict(self):
        queue = motion_one_queue if self.player == 1 else motion_two_queue

        if len(queue) < 25:
            print("function submit_input: input length is less than 25")
            return []
        
        access = (len(queue) - 20) // 2
        ave_queue = []
        for i in range(access, access+20):
            ave_queue.append(queue[i])


        in_buffer = allocate(shape=(120,), dtype=np.int32)
        out_buffer = allocate(shape=(5,), dtype=np.int32)

        for i in range(20):
            for j in range(6):
                if j < 3:
                    in_buffer[i] = unpack('i', pack('f', ave_queue[i][j] / 180))[0]
                else:
                    in_buffer[i] = unpack('i', pack('f', ave_queue[i][j] / 999))[0]

        self.dma.sendchannel.transfer(in_buffer)
        self.dma.recvchannel.transfer(out_buffer)
        self.dma.sendchannel.wait()
        self.dma.recvchannel.wait()

        out = (out_buffer[0:4])
        out = out.tolist()
        output = [0 for i in range(4)]
        can_softmax = True
        for i in range(4):
            output[i] = unpack('f', pack('i', out[i]))[0]
            if output[i] > 700: # Limit for when softmax cannot be used
                can_softmax = False
        
        if can_softmax:
            total = 0.0000001
            for val in output:
                total += exp(val)
            for i in range(len(output)):
                output[i] = exp(output[i]) / total
            print(output)
            if max(output) < 0.6:
                return INT_TO_ACTION_MAPPING[4]

        print(out)

        predicted_int = out.index(max(out))
        return INT_TO_ACTION_MAPPING[predicted_int]

    def thread_hardware_ai(self):
        global motion_one_queue
        global motion_two_queue
        global action_flag_1
        global action_flag_2
        while True:
            # Check if last action exceeds 0.5s
            if (datetime.datetime.now() - last_action_time_1).total_seconds() >= 0.5:
                action_flag_1 = True
            if (datetime.datetime.now() - last_action_time_2).total_seconds() >= 0.5:
                action_flag_2 = True

            # Clear buffer if insufficient
            if action_flag_1 and len(motion_one_queue) < 25:
                motion_one_queue.clear()
            if action_flag_2 and len(motion_two_queue) < 25:
                motion_two_queue.clear()

            # Predict action if buffer has sufficient data
            if self.player == 1 and action_flag_1 and len(motion_one_queue) >= 25:
                print("PREDICTING....")
                action_classified = self.predict()
                motion_one_queue.clear()
                if action_classified != "nil":
                    print("action classified")
                    action_one_queue.append(action_classified)
            elif self.player == 2 and action_flag_2 and len(motion_two_queue) >= 25:
                action_classified = self.predict()
                motion_two_queue.clear()
                if action_classified != "nil":
                    action_two_queue.append(action_classified)
            

def thread_debug():
    while True:
        # print("\r", "GUN 1 - ", gun_one_queue, end = "")
        # print("GUN 2 - ", gun_two_queue, end = "")
        # print("VEST 1 - ", vest_one_queue, end = "")
        # print("VEST 2 - ", vest_two_queue, end = "")
        print("\r", "MOTION 1 - ", len(motion_one_queue), "  ", end = "")
        # print("MOTION 2 - ", len(motion_two_queue), end = "")
        print("ACTION 1 - ", action_one_queue, "  ", end = "")
        # print("ACTIOM 2 - ", action_two_queue, end = "")
        # print("Motion size = ", len(motion_one_queue))
        # print(action_one_queue)

def thread_mockP1():
    while True:
        sleep(2)
        vest_one_queue.append(1)
        gun_one_queue.append(1)
        sleep(2)
        action_one_queue.append('reload')
        vest_one_queue.append(1)
        break

def thread_mockP2():
    while True:
        action_two_queue.append('shield')
        sleep(2)
        gun_two_queue.append(1)
        vest_one_queue.append(1)
        sleep(2)
        gun_two_queue.append(1)
        break

# Init global objects
ds1 = DataServer(DATA_HOST, DATA_PORT1)
ds2 = DataServer(DATA_HOST, DATA_PORT2)
# ec = EvalClient(EVAL_HOST, EVAL_PORT)
ge = GameEngine()
ai1 = HardwareAI(player=1)
ai2 = HardwareAI(player=2)

def main():
    print("GAMEMODE-", GAMEMODE)

    data_server_one_thread = Thread(target=ds1.thread_DataServer)
    data_server_two_thread = Thread(target=ds2.thread_DataServer)
    # eval_server_thread = Thread(target=ec.thread_EvalClient)
    game_engine_thread = Thread(target=ge.thread_GameEngine)
    hardware_ai_p1_thread = Thread(target=ai1.thread_hardware_ai)
    hardware_ai_p2_thread = Thread(target=ai2.thread_hardware_ai)
    # mock_test_p1_thread = Thread(target=thread_mockP1)
    # mock_test_p2_thread = Thread(target=thread_mockP2)

    # debug_thread = Thread(target=thread_debug)


    # eval_server_thread.start()
    data_server_one_thread.start()
    data_server_two_thread.start()
    game_engine_thread.start()
    hardware_ai_p1_thread.start()
    hardware_ai_p2_thread.start()
    # mock_test_p1_thread.start()
    # mock_test_p2_thread.start()
    # debug_thread.start()
    


if __name__ == "__main__":
    main()