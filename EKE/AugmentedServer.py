import socket
import logging
import sys
import json
import struct
import os
import hashlib
from Crypto.Cipher import DES3
from Crypto.Random import get_random_bytes
from diffiehellman.diffiehellman import DiffieHellman
from Interface.ProtocolServerInterface import ProtocolServerInterface

BUFFER_SIZE = 4096


def bytes_to_int(data):
    return int.from_bytes(data, byteorder=sys.byteorder)

def int_to_bytes(data, size):
    return int.to_bytes(data, size, byteorder=sys.byteorder)

def file_check(file):
    if os.path.exists(file):
        os.remove(file)

def create_json(data):
    json_data = json.dumps(data)
    json_data = json_data.zfill(len(json_data)+(8-(len(json_data) % 8)))
    json_data = json_data.encode()
    return json_data


class EKEAugmentedServer(ProtocolServerInterface):
    def __init__(self, host, port):
        self.hostname = host
        self.port = port
        self.diffie = DiffieHellman()
        self.passwords = {}
        self.public_key = None
        self.encrypted_key = None
        self.secret_key = None
        self.connection = None
        logging.basicConfig(stream=sys.stderr, level=logging.INFO)

    def start_server(self):
        """
        Function used to start the SLS server
        Once a connection is made, it creates a new thread and passes it off to a new function (handle_sls)
        :return:
        """
        self.create_public_key()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((self.hostname, self.port))
        s.listen(5)

        # Connection made
        (conn, address) = s.accept()
        self.connection = conn

        logging.debug('SERVER: Connection made with client')

    def send_file(self, path_to_file, message_size=16*1024):
        """
        Function used for sending a file with the connection that has been made. Defaults to message sizes of 16KB
        :param path_to_file:
        :param message_size:
        :return:
        """
        logging.debug('SERVER: Beginning to send', path_to_file)
        logging.debug("SERVER: sending file")
        # Going to transfer the file passed in as arg (account for \r\n w/ newline)
        with open(path_to_file, 'r+b') as f:
            data = f.read(message_size)
            while data:
                self.connection.sendall(data)

                # Try to read in more data to send
                data = f.read(message_size)
        logging.debug('SERVER: Done sending file.')


    def send_public_key(self):
        if self.public_key is None:
            self.create_public_key()
        cipher = DES3.new(self.passwords["Alice"], DES3.MODE_ECB)
        encrypted = cipher.encrypt(int_to_bytes(self.public_key, BUFFER_SIZE))

        msg = {
            "Key": bytes_to_int(encrypted)
        }
        json_msg = create_json(msg)
        logging.debug("SERVER:", json_msg)
        self.connection.sendall(json_msg)


    def create_public_key(self):
        self.diffie.generate_public_key()
        self.public_key = self.diffie.public_key
    

    def receive_public_key(self):
        data = self.waiting_for_response()
        data = data.decode()
        data = data.lstrip("0")
        msg = json.loads(data)

        cipher = DES3.new(self.passwords[msg["Name"]], DES3.MODE_ECB)
        encrypted = int_to_bytes(msg["Key"], BUFFER_SIZE)
        decrypted = bytes_to_int(cipher.decrypt(encrypted))
        if self.public_key is None:
            self.create_public_key()
        self.diffie.generate_shared_secret(decrypted)    
        self.secret_key = self.diffie.shared_key
        if self.secret_key == None:
            logging.debug("SERVER: secret key was not established")
        else:
            logging.debug("SERVER: secret key was established")


    def waiting_for_response(self):
        while True:
            data = self.connection.recv(BUFFER_SIZE*10)
            if not data:
                break
            else:
                return data

    def add_password(self, name, password):
        m = hashlib.sha1()
        m.update(password)
        x = m.digest()
        self.passwords[name] = x[:16]
