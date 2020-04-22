import ssl
import threading

from SSL.CertClient import CertClient
from SSL.CertServer import CertServer

HOST = '127.0.0.1'
PORT = 5001


def main():
    # Port and hostname that the SSL server will be running on
    host = 'localhost'
    port = 5001

    th = threading.Thread(target=run_server)
    th.start()

    # Start the client
    client = CertClient(host, port, ssl.PROTOCOL_TLS_CLIENT)
    client.connect()
    # Now transfer a file across this connection
    client.receive_file()

    th.join()


def run_server():
    # Start the server
    server = CertServer(HOST, PORT, ssl.PROTOCOL_TLS_SERVER)
    server.start_server()
    server.send_file('./SSL/util/frankenstein_book.txt')


if __name__ == "__main__":
    main()
