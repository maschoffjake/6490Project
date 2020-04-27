import socket
from Crypto.Random import get_random_bytes
from Interface.ProtocolServerInterface import ProtocolServerInterface

BUFFER_SIZE = 4096

class AugmentedServer(ProtocolServerInterface):
    def __init__(self, host, port, base, modulus):
        self.hostname = host
        self.port = port
        self.base = base
        self.modulus = modulus
        self.connection = None
        self.passwords = {}
        self.password = None

    def start_server(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((self.hostname, self.port))
        s.listen(5)
        ssock = context.wrap_socket(s, server_side=True)
        print('SERVER: listening on', self.hostname, ':', self.port, '...')

        # Connection made
        (conn, address) = ssock.accept()
        self.connection = conn
        print('SERVER: Connection made with client')
        return

    def send_file(self, path_to_file: str, message_size: int):
        return

    def add_password(self, name, password):
        self.passwords[name] = password
        return

    def waiting_for_response(self):
        while True:
            data = self.conn.recv(BUFFER_SIZE)
            if not data:
                break
            else:
                return data

    def handshake(self):
        return

