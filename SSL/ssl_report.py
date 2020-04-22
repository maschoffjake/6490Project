from SSL.CertClient import CertClient
from SSL.CertServer import CertServer

import threading
import ssl


def main():
    # Port and hostname that the SSL server will be running on
    host = 'localhost'
    port = 5001

    # Start the server
    server = CertServer(host, port, ssl.PROTOCOL_TLS_SERVER)
    server.start_server()

    # Start the client
    client = CertClient(host, port, ssl.PROTOCOL_TLS_CLIENT)
    client.connect()

    # Now transfer a file across this connection
    # client.receive_file()
    server.send_file('./util/frankenstein_book.txt')


if __name__ == "__main__":
    main()