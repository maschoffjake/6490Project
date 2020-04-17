'''
    Client that is used for making connection with 
'''
import ssl
import socket

# Libraries for timing/power/utilization
import pyRAPL


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

    # Create the SSL context for the SSL connection to be made
    def create_ssl_context(self):
        self.context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        self.context.load_cert_chain('./util/client_certificate.pem', './util/client_key.pem')
        self.context.check_hostname = False
        self.context.verify_mode = ssl.CERT_NONE        # Need to set this flag since we are using a self-signed certificate
        # context.set_ciphers('TLS_AES_256_GCM_SHA384')       # Recommended cipher from https://www.openssl.org/docs/man1.0.2/man1/ciphers.html

    # Function used to connect to a server that is listening on the given hostname and port
    def connect(self):
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

    # Set up the power consumption recorder
    pyRAPL.setup()
    csv_output = pyRAPL.outputs.CSVOutput('TLS_power_results.csv')

    # Start the client
    client = ssl_client(HOST, PORT)
    client.create_ssl_context()

    meter = pyRAPL.Measurement('bar')
    meter.begin()
    # Time the connection for TCP and SSL setup
    client.connect()
    meter.end()
    meter.export(csv_output)

    # Now transfer a file across this connection
    client.receive_file()

    csv_output.save()

if __name__ == "__main__":
    main()
