import socket
import sys
import logging
import json
import hashlib
from Crypto.Cipher import DES3
from diffiehellman.diffiehellman import DiffieHellman
from Interface.ProtocolClientInterface import ProtocolClientInterface

BUFFER_SIZE = 4096

def bytes_to_int(data):
    return int.from_bytes(data, byteorder=sys.byteorder)

def int_to_bytes(data, size):
    return int.to_bytes(data, size, byteorder=sys.byteorder)

def create_json(data):
    json_data = json.dumps(data)
    json_data = json_data.zfill(len(json_data)+(8-(len(json_data) % 8)))
    json_data = json_data.encode()
    return json_data


class EKEAugmentedClient(ProtocolClientInterface):
    def __init__(self, host, port, password):
        self.hostname = host
        self.port = port
        self.diffie = DiffieHellman()
        self.password = password
        self.public_key = None
        self.encrypted_key = None
        self.secret_key = None
        self.socket = None
        self.data = None

    def connect(self):
        """
        Function used to connect to a server that is listening on the given hostname and port
        :return:
        """
        print("CLIENT: Connecting to server...")
        self.create_public_key()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.hostname, self.port))
        print("CLIENT: Connected to server...")
        return

    def receive_file(self, message_size=16*1024):
        """
        Function used for receiving a file from the connection made, defaults to 16KB sized messages
        :param message_size:
        :return:
        """
        logging.debug('CLIENT: Beginning to receive.')
        print("CLIENT: receiving file")
        total_data = []
        data = self.socket.recv(message_size)
        while data != bytes(''.encode()):
            total_data.append(data)
            data = self.socket.recv(message_size)
        print("CLIENT: received file")

        logging.debug('CLIENT: Done receiving file')

    def send_public_key(self):
        if self.public_key is None:
            self.create_public_key()
        m = hashlib.sha1()
        m.update(self.password)
        x = m.digest()
        cipher = DES3.new(x[:16], DES3.MODE_ECB)
        encrypted = cipher.encrypt(int_to_bytes(self.public_key, BUFFER_SIZE))
        #self.socket.sendall(encrypted)

        msg = {
            "Name": "Alice",
            "Key": bytes_to_int(encrypted)
        }
        json_msg = create_json(msg)
        self.socket.sendall(json_msg)
        #self.socket.sendall(int_to_bytes(self.public_key, BUFFER_SIZE))

    def create_public_key(self):
        self.diffie.generate_public_key()
        self.public_key = self.diffie.public_key

    def receive_public_key(self):
        data = self.waiting_for_response()
        data = data.decode()
        data = data.lstrip("0")
        print("CLIENT:", data)
        msg = json.loads(data)

        m = hashlib.sha1()
        m.update(self.password)
        x = m.digest()
        cipher = DES3.new(x[:16], DES3.MODE_ECB)
        encrypted = int_to_bytes(msg["Key"], BUFFER_SIZE)
        decrypted = bytes_to_int(cipher.decrypt(encrypted))
        if self.public_key is None:
            self.create_public_key()
        self.diffie.generate_shared_secret(decrypted)    
        self.secret_key = self.diffie.shared_key
        if self.secret_key == None:
            print("CLIENT: secret key was not established")
        else:
            print("CLIENT: secret key was established")


    def waiting_for_response(self):
        while True:
            data = self.socket.recv(BUFFER_SIZE*10)
            if not data:
                break
            else:
                return data

