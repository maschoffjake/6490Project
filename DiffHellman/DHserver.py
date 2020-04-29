import base64
import os
import socket
import pyDH
import sys
import logging

from Interface.ProtocolServerInterface import ProtocolServerInterface
from DiffHellman.DHContext import getPublicKey, getPrivateKey, encryptContent, verifyContent, hashContent, ca_sign_key
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding


class DHServer(ProtocolServerInterface):
    ANONYMOUS = 0            # STANDARD DIFFIE HELLMAN EXCHANGE
    AUTHENTICATED = 1       # CERTIFICATE AUTHENTICATED EXCHANGE
    STS = 2                 # ASYMMETRIC KEY AUTHENTICATION

    def __init__(self, hostname, port, protocol):
        dir_path = os.path.dirname(os.path.realpath(__file__)) + '/util/'
        self.hostname = hostname
        self.port = port
        self.protocol = protocol
        self.context = pyDH.DiffieHellman()
        self.connection = None
        self.certificate = (base64.b64encode(ca_sign_key(dir_path + 'server_key.pem', dir_path + 'ca_priv_key.pem'))).decode("utf-8")
        self.private_key = getPrivateKey(dir_path + 'server_key.pem')
        self.station_pub_key = getPrivateKey(dir_path + 'client_key.pem').public_key() if protocol == DHServer.STS else None
        logging.basicConfig(stream=sys.stderr, level=logging.INFO)

    def start_server(self):
        """
        Function used to start the SLS server
        Once a connection is made, it creates a new thread and passes it off to a new function (handle_sls)
        :return:
        """
        # Load certificates from 'default CA'
        #context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        dir_path = os.path.dirname(os.path.realpath(__file__))
        #context.load_cert_chain(dir_path + '/util/server_certificate.pem', dir_path + '/util/server_key.pem')
        # Recommended cipher taken from https://www.openssl.org/docs/man1.0.2/man1/ciphers.html
        # context.set_ciphers('TLS_AES_256_GCM_SHA384')
        # context.load_verify_locations(capath='./util/')
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self.hostname, self.port))
        sock.listen(5)
        logging.debug('SERVER: DH server is listening on', self.hostname, ':', self.port, '...')
        conn, addr = sock.accept()
        self.connection = self.handshake(conn)
        logging.debug('SERVER: Connection made with client')

    def send_file(self, path_to_file, message_size=16*1024):
        """
        Function used for sending a file with the connection that has been made. Defaults to message sizes of 16KB
        :param path_to_file:
        :param message_size:
        :return:
        """
        logging.debug('SERVER: Beginning to send', path_to_file)
        conn, key = self.connection

        # Going to transfer the file passed in as arg (account for \r\n w/ newline)
        with open(path_to_file, 'r+b') as f:
            data = f.read(message_size)

        iv = hashContent(key)[0:16]
        message_hash = hashContent(data)
        package = data + b',' + message_hash
        enc_message = encryptContent(package, key, iv)

        while True:
            data = conn.recv(4096)
            if data == b'READY':
                break

        conn.sendall(enc_message)
        logging.debug('SERVER: Done sending file.')

    # CONNECTION HELPER METHOD
    # RETURN TUPLE (SOCK, SESSION KEY)
    def handshake(self, sock):
        # RCV TA
        while True:
            data = sock.recv(4096)
            # logging.debug(data)
            if b'\n\n' in data:
                break

        message = data.rsplit(b'\n\n')[0]

        if self.protocol == DHServer.STS:
            try:
                message, b64_hash = message.decode().split(',')
                enc_hash = base64.b64decode(b64_hash.encode())
                rcv_hash = self.private_key.decrypt(enc_hash,
                                                   padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),
                                                                algorithm=hashes.SHA256(),
                                                                label=None)).decode("utf-8")
                r_hash = base64.b64decode(rcv_hash.encode())
                message = message.encode()
                if hashContent(message) != r_hash:
                    raise Exception("Sent key and hash do not match.")
            except Exception as e:
                logging.debug('SERVER STS ERROR FROM CLIENT:\t{}'.format(e))
                return

        #logging.debug('SERVER: {}'.format(message.decode()))
        rcv_pub_key = int(message.decode(), base=10)
        # GENERATE TB
        dh_public_key = self.context.gen_public_key()

        # GENERATE SESSION KEY
        try:
            dh_shared_key = self.context.gen_shared_key(rcv_pub_key)
            session_key = str(dh_shared_key).encode()[0:32]
        except Exception as e:
            logging.debug('SERVER ERROR:\t{}'.format(e))
            return

        # SEND TA
        #message = str(dh_public_key) + '\n\n'
        #sock.send(message.encode())

        # IF ANONYMOUS DONE
        if self.protocol == DHServer.ANONYMOUS:
            # SEND AS IS
            message = str(dh_public_key) + '\n\n'
            sock.send(message.encode())

        elif self.protocol == DHServer.AUTHENTICATED:
            # VERIFY WITH CERTIFICATE
            message = str(dh_public_key)
            pub_key_bytes = self.private_key.public_key().public_bytes(encoding=serialization.Encoding.PEM,
                                                          format=serialization.PublicFormat.SubjectPublicKeyInfo)
            b64_pub_key = pub_key_bytes.decode("utf-8")
            message += ',' + b64_pub_key + ',' + self.certificate + '\n\n'
            sock.send(message.encode())
        else:
            message = str(dh_public_key)
            m_hash = base64.b64encode(hashContent(message.encode()))
            enc_hash = self.station_pub_key.encrypt(m_hash,
                                                    padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),
                                                                 algorithm=hashes.SHA256(),
                                                                 label=None))
            b64_hash = (base64.b64encode(enc_hash)).decode("utf-8")
            message += ',' + b64_hash + '\n\n'
            sock.sendall(message.encode())

        return sock, session_key
