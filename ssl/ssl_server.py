'''
    Server using SSL that is waiting for connections to be made
'''
import ssl
import socket
import threading

# Port and hostname that the SSL server will be running on
HOST = 'localhost'
PORT = 5001

class ssl_server:
    def __init__(self, hostname, port):
        self.hostname = hostname
        self.port = port
        self.hostname_str = hostname + ':' + str(port)

    # Function used to start the SLS server
    # Once a connection is made, it creates a new thread
    # and passes it off to a new function (handle_sls)
    def start_server(self):

        # Load certificates from 'default CA'
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain('./util/server_certificate.pem', './util/server_key.pem')
        # context.set_ciphers('TLS_AES_256_GCM_SHA384')       # Recommended cipher taken from https://www.openssl.org/docs/man1.0.2/man1/ciphers.html
        # context.load_verify_locations(capath='./util/')
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((self.hostname, self.port))
        s.listen(5)
        ssock = context.wrap_socket(s, server_side=True)
        print('SERVER:SSL server is listening on', self.hostname_str)

        # Connection made
        (conn, address) = ssock.accept()
        self.conn = conn
        print('SERVER:Connection made with server')

    # Function used for sending a file with the connection that has been made. Defaults to message sizes of 16KB
    def send_file(self, filename, message_size=16*1024):
        print('SERVER:Beginning to send', filename)
        # Going to transfer the file passed in as arg (account for \r\n w/ newline)
        with open(filename, 'r+b') as f:
            data = f.read(message_size)
            while data:
                self.conn.sendall(data)

                # Try to read in more data to send
                data = f.read(message_size)
        print('SERVER:Done sending file')

# Run the server
def main():

    # Start the server
    server = ssl_server(HOST, PORT)
    server.start_server()

    # Now transfer a file across this connection
    server.send_file('./util/frankenstein_book.txt')

if __name__ == "__main__":
    main()