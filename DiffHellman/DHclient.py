import base64
import os
import pyDH
import socket

from Interface.ProtocolClientInterface import ProtocolClientInterface
from DiffHellman.DHContext import getPublicKey, encryptContent, verifyContent, hashContent


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
        self.hostname = hostname
        self.port = port
        self.protocol = protocol
        # Dont need a context wrapper like SSL
        self.cert = None
        self.version = None
        self.context = self.create_dh_context()
        self.ssock = None



    def create_dh_context(self):
        """
        Create the DH context for the tcp connection to be made
        """
        print("CLIENT: Creating DH Context")
        dir_path = os.path.dirname(os.path.realpath(__file__))
        key_path = dir_path + '/util/server_key.pem'

        if self.protocol == DHClient.ANONYMOUS:
            self.version = "ANONYMOUS DH"
            return pyDH.DiffieHellman()
        elif self.protocol == DHClient.AUTHENTICATED:
            self.version = "CERTIFICATE AUTHENTICATED DH"
            self.cert = None
            return pyDH.DiffieHellman()
        elif self.protocol == DHClient.STS:
            self.version = "PUBLIC KEY AUTHENTICATED DH"
            self.cert = getPublicKey(key_path)
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
        print("CLIENT: Connecting to server...")
        sock = socket.create_connection((self.hostname, self.port))
        # Commence HANDSHAKE TO GENERATE SESSION KEY, REPORT COMPLETION
        self.ssock = self.handshake(sock)
        #self.ssock = self.context.wrap_socket(sock, server_hostname='localhost')
        print("CLIENT: Connected to server.\n"
              "CLIENT: DH version: {}".format(self.version))

    def receive_file(self, message_size=16*1024):
        """
        Function used for receiving a file from the connection made, defaults to 16KB sized messages
        :param message_size:
        :return:
        """
        print('CLIENT: Beginning to receive.')
        conn, key = self.ssock
        message = b''
        #data = self.ssock.recv(message_size)
        while True:
            data = conn.recv(4096)
            if not data:
                break
            message += data


        decrypted_message, verified = verifyContent(message, key)

        if verified:
            print('CLIENT: Done receiving file')
        else:
            print('CLIENT: ERROR RECEIVING MESSAGE')

    # RETURN TUPLE (SOCK, SESSION KEY)
    def handshake(self, sock):
        # GENERATE & SEND TA
        dh_public_key = self.context.gen_public_key()
        message = str(dh_public_key) + '\n'
        #print('CLIENT: {}'.format(message))
        sock.send(message.encode())

        # RCV TB
        while True:
            data = sock.recv(4096)
            # print(data)
            if not data or b'\n' in data:
                break

        message = data.rsplit(b'\n')[0]
        rcv_pub_key = int(message.decode(), base=10)
        # GENERATE SESSION KEY
        try:
            dh_shared_key = self.context.gen_shared_key(rcv_pub_key)
        except Exception as e:
            print('ERROR:\t{}'.format(e))
            return


        # IF ANONYMOUS DONE
        if self.protocol == DHClient.ANONYMOUS:
            return sock, str(dh_shared_key).encode()[0:32]


        # RCV SESSION KEY FOR VERIFICATION
        while True:
            data = sock.recv(4096)
            # print(data)
            if not data:
                break

        try:
            print("NOT IMPLEMENTED")
            #dcpt_data = dhc.verifyContents()
            #data = base64.b64decode(data.encode())
            #dig_sig, hash_sig = data.split(',')
            # CONVERT BACK TO BYTES, THEN DECODE FROM BASE64 CONVERSION
            #bob_certificate_bytes = base64.b64decode(dig_sig.encode())
            #hash_sig = base64.b64decode(hash_sig.encode())
        except Exception as e:
            print("SOMETHING WENT TERRIBLY WRONG: {}".format(e))
            return None

        # VERIFY SESSION KEY
        if self.protocol == DHClient.AUTHENTICATED:
            # VERIFY WITH CERTIFICATE
            return None
        else:
            # VERIFY WITH ASYMMETRIC KEY
            return None