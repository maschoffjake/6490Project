import socket
import sys
import logging
from diffiehellman.diffiehellman import DiffieHellman
from Interface.ProtocolClientInterface import ProtocolClientInterface

BUFFER_SIZE = 4096

def bytes_to_int(data):
    return int.from_bytes(data, byteorder=sys.byteorder)

def int_to_bytes(data, size):
    return int.to_bytes(data, size, byteorder=sys.byteorder)

class DiffieClient(ProtocolClientInterface):
    def __init__(self, port, host):
        self.hostname = host
        self.port = port
        self.diffie = DiffieHellman()
        self.public_key = None
        self.secret_key = None
        self.socket = None

    def connect(self):
        """
        Function used to connect to a server that is listening on the given hostname and port
        :return:
        """
        print("CLIENT: Connecting to server...")
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.hostname, self.port))
        print("CLIENT: Connected to server...")
        return

    def receive_file(self, message_size: int):
        """
        Function used for receiving a file from the connection made, defaults to 16KB sized messages
        :param message_size:
        :return:
        """
        logging.debug('CLIENT: Beginning to receive.')
        total_data = []
        data = self.ssock.recv(message_size)
        while data != bytes(''.encode()):
            total_data.append(data)
            data = self.ssock.recv(message_size)

        logging.debug('CLIENT: Done receiving file')

    def send_public_key(self):
        self.diffie.generate_public_key()
        self.socket.sendall(int_to_bytes(self.diffie.public_key, 1024))

    def create_public_key(self):
        self.public_key = self.diffie.generate_public_key()

    def receive_public_key(self):
        data = self.waiting_for_response()
        self.secret_key = self.diffie.generate_public_key(data)


    def waiting_for_response(self):
        while True:
            data = self.socket.recv(BUFFER_SIZE)
            if not data:
                break
            else:
                return data

