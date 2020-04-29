import base64
import os
import pyDH
import socket
import sys
import logging

from Interface.ProtocolClientInterface import ProtocolClientInterface
from DiffHellman.DHContext import getPublicKey, getPrivateKey, encryptContent, verifyContent, hashContent
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from cryptography.hazmat.backends import default_backend


class DHClient(ProtocolClientInterface):
    ANONYMOUS = 0            # STANDARD DIFFIE HELLMAN EXCHANGE
    AUTHENTICATED = 1       # CERTIFICATE AUTHENTICATED EXCHANGE
    STS = 2                 # ASYMMETRIC KEY AUTHENTICATION

    def __init__(self, hostname, port, protocol):
        """
        Set hostname, port, protocol
        :param hostname: Hostname of this client
        :param port: Port of this client
        :param protocol: Protocol to use for this client
        """
        dir_path = os.path.dirname(os.path.realpath(__file__)) + '/util/'
        self.hostname = hostname
        self.port = port
        self.protocol = protocol
        # Dont need a context wrapper like SSL
        self.version = None
        self.context = self.create_dh_context()
        self.ssock = None
        self.station_pub_key = getPrivateKey(dir_path + 'server_key.pem').public_key() if protocol == DHClient.STS or \
                                                                                          protocol == DHClient.AUTHENTICATED else None
        self.client_private_key = getPrivateKey(dir_path + 'client_key.pem') if protocol == DHClient.STS else None
        self.ca_key = getPublicKey(dir_path + 'ca_pub_key.pem') if protocol == DHClient.AUTHENTICATED else None
        logging.basicConfig(stream=sys.stderr, level=logging.INFO)

    def create_dh_context(self):
        """
        Create the DH context for the tcp connection to be made
        """
        logging.debug("CLIENT: Creating DH Context")
        dir_path = os.path.dirname(os.path.realpath(__file__))
        key_path = dir_path + '/util/server_key.pem'

        if self.protocol == DHClient.ANONYMOUS:
            self.version = "ANONYMOUS DH"
            return pyDH.DiffieHellman()
        elif self.protocol == DHClient.AUTHENTICATED:
            self.version = "CERTIFICATE AUTHENTICATED DH"
            return pyDH.DiffieHellman()
        elif self.protocol == DHClient.STS:
            self.version = "PUBLIC KEY AUTHENTICATED DH"
            return pyDH.DiffieHellman()
        else:
            raise Exception("That protocol is not currently supported.")

        #context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        #dir_path = os.path.dirname(os.path.realpath(__file__))
        #clientAuth = dir_path + '/util/SOME_CERTIFICATE_OR_KEY_HERE'
        #context.load_cert_chain(dir_path + '/util/client_certificate.pem', dir_path + '/util/client_key.pem')
        #context.check_hostname = False
        # Need to set this flag since we are using a self-signed certificate
        #context.verify_mode = ssl.CERT_NONE
        # Recommended cipher from https://www.openssl.org/docs/man1.0.2/man1/ciphers.html
        # context.set_ciphers('TLS_AES_256_GCM_SHA384')
        #return context

    def connect(self):
        """
        Function used to connect to a server that is listening on the given hostname and port
        :return:
        """
        logging.debug("CLIENT: Connecting to server...")
        sock = socket.create_connection((self.hostname, self.port))
        # Commence HANDSHAKE TO GENERATE SESSION KEY, REPORT COMPLETION
        self.ssock = self.handshake(sock)
        #self.ssock = self.context.wrap_socket(sock, server_hostname='localhost')
        logging.debug("CLIENT: Connected to server.\n"
              "CLIENT: DH version: {}".format(self.version))

    def receive_file(self, message_size=16*1024):
        """
        Function used for receiving a file from the connection made, defaults to 16KB sized messages
        :param message_size:
        :return:
        """
        logging.debug('CLIENT: Beginning to receive.')
        conn, key = self.ssock
        conn.send('READY'.encode())
        message = b''
        #data = self.ssock.recv(message_size)
        while True:
            data = conn.recv(4096)
            if not data:
                break
            message += data


        decrypted_message, verified = verifyContent(message, key)

        if verified:
            logging.debug('CLIENT: Done receiving file')
        else:
            logging.debug('CLIENT: ERROR RECEIVING MESSAGE')

    # RETURN TUPLE (SOCK, SESSION KEY)
    def handshake(self, sock):
        # GENERATE & SEND TA
        dh_public_key = self.context.gen_public_key()

        if self.protocol == DHClient.STS:
            message = str(dh_public_key)
            m_hash = base64.b64encode(hashContent(message.encode()))
            enc_hash = self.station_pub_key.encrypt(m_hash,
                                                    padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),
                                                                 algorithm=hashes.SHA256(),
                                                                 label=None))
            b64_hash = (base64.b64encode(enc_hash)).decode("utf-8")
            message += ',' + b64_hash + '\n\n'
            sock.send(message.encode())
        else:
            message = str(dh_public_key) + '\n\n'
            #logging.debug('CLIENT: {}'.format(message))
            sock.send(message.encode())

        # RCV TB
        while True:
            data = sock.recv(4096)
            # logging.debug(data)
            if b'\n\n' in data:
                break

        message = data.rsplit(b'\n\n')[0]

        if self.protocol == DHClient.STS:
            try:
                message, b64_hash = message.decode().split(',')
                message = message.encode()
                enc_hash = base64.b64decode(b64_hash.encode())
                rcv_hash = self.client_private_key.decrypt(enc_hash,
                                                    padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),
                                                                 algorithm=hashes.SHA256(),
                                                                 label=None)).decode("utf-8")
                r_hash = base64.b64decode(rcv_hash.encode())
                if hashContent(message) != r_hash:
                    raise Exception("Sent key and hash do not match.")
            except Exception as e:
                logging.debug('CLIENT STS ERROR FROM SERVER:\t{}'.format(e))
                return

        elif self.protocol == DHClient.AUTHENTICATED:
            message, pub_key, dig_sig = message.decode().split(',')
            message = message.encode()
            try:
                cert = base64.b64decode(dig_sig.encode())
                self.ca_key.verify(cert, pub_key.encode(),
                                   padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
                                   hashes.SHA256())
            except Exception as e:
                logging.debug('CLIENT CERTIFICATE FROM SERVER ERROR:\t{}'.format(e))
                return

        rcv_pub_key = int(message.decode(), base=10)
        # GENERATE SESSION KEY
        try:
            dh_shared_key = self.context.gen_shared_key(rcv_pub_key)
            session_key = str(dh_shared_key).encode()[0:32]
        except Exception as e:
            logging.debug('ERROR:\t{}'.format(e))
            return

        return sock, session_key
