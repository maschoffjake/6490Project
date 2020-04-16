'''
    Client that is used for making connection with 
'''
import ssl
import socket

# Port and hostname that the SSL server will be running on
HOST = 'localhost'
PORT = 5001

#
# Takes in the hostname and the port to connect to (server address/port)
#
class ssl_client():
    def __init__(self, hostname, port):
        self.hostname = hostname
        self.port = port
        self.hostname_str = self.hostname + ':' + str(self.port)

    # Function used to connect to a server that is listening on the given hostname and port
    def connect(self):
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.load_cert_chain('./util/client_certificate.pem', './util/client_key.pem')
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        # context.set_ciphers('TLS_AES_256_GCM_SHA384')       # Recommended cipher from https://www.openssl.org/docs/man1.0.2/man1/ciphers.html
        print('CLIENT:Connecting to server')
        s = socket.create_connection((self.hostname, self.port))
        self.ssock = context.wrap_socket(s, server_hostname='localhost')        # Third flag is for do_handshake on connect, maybe toy around with this for just handshake?

    # Function used for receiving a file from the connection made, defaults to 16KB sized messages
    def receive_file(self, message_size=16*1024):
        self.total_data = []
        data = self.ssock.recv(message_size)
        while data != bytes(''.encode()):
            self.total_data.append(data)
            data = self.ssock.recv(message_size)

        print('CLIENT:Done receeiving file')
        print('CLIENT:File received (truncated):', self.total_data[:40])

# Run the client
def main():

    # Start the client
    client = ssl_client(HOST, PORT)
    client.connect()

    # Now transfer a file across this connection
    client.receive_file()

if __name__ == "__main__":
    main()
