import os
import ssl
import socket
import logging
import sys

from Interface.ProtocolServerInterface import ProtocolServerInterface


class CertServer(ProtocolServerInterface):
    def __init__(self, hostname, port, protocol):
        self.hostname = hostname
        self.port = port
        self.protocol = protocol
        self.connection = None
        logging.basicConfig(stream=sys.stderr, level=logging.INFO)

    def start_server(self):
        """
        Function used to start the SLS server
        Once a connection is made, it creates a new thread and passes it off to a new function (handle_sls)
        :return:
        """
        # Load certificates from 'default CA'
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        dir_path = os.path.dirname(os.path.realpath(__file__))
        context.load_cert_chain(dir_path + '/util/server_certificate.pem', dir_path + '/util/server_key.pem')
        # Recommended cipher taken from https://www.openssl.org/docs/man1.0.2/man1/ciphers.html
        # context.set_ciphers('TLS_AES_256_GCM_SHA384')
        # context.load_verify_locations(capath='./util/')
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((self.hostname, self.port))
        s.listen(5)
        ssock = context.wrap_socket(s, server_side=True)
        logging.debug('SERVER: SSL server is listening on', self.hostname, ':', self.port, '...')

        # Connection made
        (conn, address) = ssock.accept()
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
        # Going to transfer the file passed in as arg (account for \r\n w/ newline)
        with open(path_to_file, 'r+b') as f:
            data = f.read(message_size)
            while data:
                self.connection.sendall(data)

                # Try to read in more data to send
                data = f.read(message_size)
        logging.debug('SERVER: Done sending file.')
