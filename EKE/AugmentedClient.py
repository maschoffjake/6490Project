import socket
import json
import random
import sys
from Crypto.Cipher import DES3
from Crypto.Random import get_random_bytes
from Interface.ProtocolClientInterface import ProtocolClientInterface

BUFFER_SIZE = 4096

class AugmentedClient(ProtocolClientInterface):
    def __init__(self, host, port, password, base, modulus):
        """
        Set hostname, port, protocol
        :param hostname: Hostname of this client
        :param port: Port of this client
        :param base: base value for discrete logarithm
        :param modulus: modulus value for discrete logarithm
        :param password: shared password between client and server
        """
        self.hostname = host
        self.port = port
        self.base = base
        self.modulus = modulus
        self.password = password
        self.cipher = None
        self.random = None
        self.socket = None


    def connect(self):
        """
        Function used to connect to a server that is listening on the given hostname and port
        :return:
        """
        print("CLIENT: Connecting to server...")
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))
        print("CLIENT: Connected to server...")
        return

    
    def handshake(self):
        self.create_cipher()
        rand = random.randint(0, 100)
        RA = self.base ** rand % self.modulus
        msg = self.cipher.encode(RA)
        message_1 = {
            "Name": "Alice",
            "Message": int.from_bytes(msg, byteorder=sys.byteorder)
        }
        return


    def waiting_for_response(self):
        while True:
            data = self.socket.recv(BUFFER_SIZE)
            if not data:
                break
            else:
                return data


    def create_json(self, data):
        json_data = json.dumps(data)
        json_data = json_data.zfill(len(json_data)+(8-(len(json_data) % 8)))
        json_data = json_data.encode()
        return json_data

    def create_cipher(self):
        self.cipher = DES3.new(self.password, DES3.MODE_ECB, 'This is an IV')

    
    def bytes_to_int(data):
        return int.from_bytes(data, byteorder=sys.byteorder)

    def int_to_bytes(data, size):
        return int.to_bytes(data, size, byteorder=sys.byteorder)

    def receive_file(self, message_size: int):
        return