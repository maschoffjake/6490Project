import os
import ssl
import socket
from Interface.ProtocolClientInterface import ProtocolClientInterface


class CertClient(ProtocolClientInterface):
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
        self.context = self.create_ssl_context()
        self.ssock = None

    @staticmethod
    def create_ssl_context():
        """
        Create the SSL context for the SSL connection to be made
        """
        print("CLIENT: Creating SSL Context")
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        dir_path = os.path.dirname(os.path.realpath(__file__))
        context.load_cert_chain(dir_path + '/util/client_certificate.pem', dir_path + '/util/client_key.pem')
        context.check_hostname = False
        # Need to set this flag since we are using a self-signed certificate
        context.verify_mode = ssl.CERT_NONE
        # Recommended cipher from https://www.openssl.org/docs/man1.0.2/man1/ciphers.html
        # context.set_ciphers('TLS_AES_256_GCM_SHA384')
        return context

    def connect(self):
        """
        Function used to connect to a server that is listening on the given hostname and port
        :return:
        """
        print("CLIENT: Connecting to server...")
        s = socket.create_connection((self.hostname, self.port))
        # Third flag is for do_handshake on connect, maybe toy around with this for just handshake?
        self.ssock = self.context.wrap_socket(s, server_hostname='localhost')
        print("CLIENT: Connected to server.")

    def receive_file(self, message_size=16*1024):
        """
        Function used for receiving a file from the connection made, defaults to 16KB sized messages
        :param message_size:
        :return:
        """
        print('CLIENT: Beginning to receive.')
        total_data = []
        data = self.ssock.recv(message_size)
        while data != bytes(''.encode()):
            total_data.append(data)
            data = self.ssock.recv(message_size)

        print('CLIENT: Done receiving file')
        # print('CLIENT: File received (truncated):', total_data[:40])
