import socket
import logging
import sys
import json
import struct
import os
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


class EKEDiffieServer(ProtocolServerInterface):
    def __init__(self, host, port):
        self.hostname = host
        self.port = port
        self.diffie = DiffieHellman()
        self.passwords = {}
        self.public_key = None
        self.encrypted_key = None
        self.secret_key = None
        self.connection = None


    def start_server(self):
        """
        Function used to start the SLS server
        Once a connection is made, it creates a new thread and passes it off to a new function (handle_sls)
        :return:
        """
        self.create_public_key()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        s.bind((self.hostname, self.port))
        s.listen(5)

        # Connection made
        (conn, address) = s.accept()
        self.connection = conn

        print('SERVER: Connection made with client')

    def send_file(self, path_to_file, message_size=16*1024):
        """
        Function used for sending a file with the connection that has been made. Defaults to message sizes of 16KB
        :param path_to_file:
        :param message_size:
        :return:
        """
        logging.debug('SERVER: Beginning to send', path_to_file)
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
        self.connection.sendall(int_to_bytes(self.public_key, BUFFER_SIZE))


    def create_public_key(self):
        self.diffie.generate_public_key()
        self.public_key = self.diffie.public_key
    

    def receive_public_key(self):
        data = self.waiting_for_response()
        data = data.decode()
        data = data.lstrip("0")
        msg = json.loads(data)

        cipher = DES3.new(self.passwords[msg["Name"]], DES3.MODE_ECB, 'This is an IV')
        encrypted = int_to_bytes(msg["Key"], BUFFER_SIZE)
        decrypted = bytes_to_int(cipher.decrypt(encrypted))
        if self.public_key is None:
            self.create_public_key()
        self.diffie.generate_shared_secret(decrypted)    
        self.secret_key = self.diffie.shared_key
        if self.secret_key == None:
            print("SERVER: secret key was not established")
        else:
            print("SERVER: secret key was established")


    def waiting_for_response(self):
        while True:
            data = self.connection.recv(BUFFER_SIZE*10)
            if not data:
                break
            else:
                return data

    def add_password(self, name, password):
        self.passwords[name] = password

    '''
    Author and code for this methods was written and belong to
    https://eli.thegreenplace.net/2010/06/25/aes-encryption-of-files-in-python-with-pycrypto
    '''
    def encrypt_file(self, key, in_filename, out_filename=None, chunksize=64*1024):
        ''' Encrypts a file using AES (CBC mode) with the
        given key.

        key:
            The encryption key - a string that must be
            either 16, 24 or 32 bytes long. Longer keys
            are more secure.

        in_filename:
            Name of the input file

        out_filename:
            If None, '<in_filename>.enc' will be used.

        chunksize:
            Sets the size of the chunk which the function
            uses to read and encrypt the file. Larger chunk
            sizes can be faster for some files and machines.
            chunksize must be divisible by 16.
        '''
        key = key.encode()
        key = key[0:24].decode()
        if not out_filename:
            out_filename = in_filename + '.enc'

        iv = get_random_bytes(16)
        encryptor = DES3.new(key, DES3.MODE_ECB, iv)
        filesize = os.path.getsize(in_filename)

        with open(in_filename, 'rb') as infile:
            with open(out_filename, 'wb') as outfile:
                outfile.write(struct.pack('<Q', filesize))
                outfile.write(iv)

                while True:
                    chunk = infile.read(chunksize)
                    if len(chunk) == 0:
                        break
                    elif len(chunk) % 16 != 0:
                        chunk += ' ' * (16 - len(chunk) % 16)

                    outfile.write(encryptor.encrypt(chunk))
        return

    def file_check(self, file):
        if os.path.exists(file):
            os.remove(file)
