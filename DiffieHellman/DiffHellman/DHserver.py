import os
import ssl
import socket
import pyDH

from Interface.ProtocolServerInterface import ProtocolServerInterface
from DiffHellman.DHContext import getPublicKey, encryptContent, verifyContent, hashContent


class DHServer(ProtocolServerInterface):
    ANONYMOUS = 0            # STANDARD DIFFIE HELLMAN EXCHANGE
    AUTHENTICATED = 1       # CERTIFICATE AUTHENTICATED EXCHANGE
    STS = 2                 # ASYMMETRIC KEY AUTHENTICATION

    def __init__(self, hostname, port, protocol):
        self.hostname = hostname
        self.port = port
        self.protocol = protocol
        self.context = pyDH.DiffieHellman()
        self.connection = None

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
        print('SERVER: DH server is listening on', self.hostname, ':', self.port, '...')
        conn, addr = sock.accept()
        self.connection = self.handshake(conn)
        print('SERVER: Connection made with client')

    def send_file(self, path_to_file, message_size=16*1024):
        """
        Function used for sending a file with the connection that has been made. Defaults to message sizes of 16KB
        :param path_to_file:
        :param message_size:
        :return:
        """
        print('SERVER: Beginning to send', path_to_file)
        conn, key = self.connection

        # Going to transfer the file passed in as arg (account for \r\n w/ newline)
        with open(path_to_file, 'r+b') as f:
            data = f.read(message_size)

        iv = hashContent(key)[0:16]
        message_hash = hashContent(data)
        package = data + b',' + message_hash
        enc_message = encryptContent(package, key, iv)
        conn.sendall(enc_message)
        print('SERVER: Done sending file.')

    # CONNECTION HELPER METHOD
    # RETURN TUPLE (SOCK, SESSION KEY)
    def handshake(self, sock):
        # RCV TA
        while True:
            data = sock.recv(4096)
            # print(data)
            if not data or b'\n' in data:
                break

        message = data.rsplit(b'\n')[0]
        #print('SERVER: {}'.format(message.decode()))
        rcv_pub_key = int(message.decode(), base=10)
        # GENERATE TB
        dh_public_key = self.context.gen_public_key()

        # GENERATE SESSION KEY
        try:
            dh_shared_key = self.context.gen_shared_key(rcv_pub_key)
        except Exception as e:
            print('ERROR:\t{}'.format(e))
            return

        # SEND TA
        message = str(dh_public_key) + '\n'
        sock.send(message.encode())

        # IF ANONYMOUS DONE
        if self.protocol == DHServer.ANONYMOUS:
            return sock, str(dh_shared_key).encode()[0:32]

        # RCV SESSION KEY FOR VERIFICATION
        while True:
            data = sock.recv(4096)
            # print(data)
            if not data:
                break

        try:
            print("NOT IMPLEMENTED")
            # dcpt_data = dhc.verifyContents()
            # data = base64.b64decode(data.encode())
            # dig_sig, hash_sig = data.split(',')
            # CONVERT BACK TO BYTES, THEN DECODE FROM BASE64 CONVERSION
            # bob_certificate_bytes = base64.b64decode(dig_sig.encode())
            # hash_sig = base64.b64decode(hash_sig.encode())
        except Exception as e:
            print("SOMETHING WENT TERRIBLY WRONG: {}".format(e))
            return None

        # VERIFY SESSION KEY
        if self.protocol == DHServer.AUTHENTICATED:
            # VERIFY WITH CERTIFICATE
            return None
        else:
            # VERIFY WITH ASYMMETRIC KEY
            return None
