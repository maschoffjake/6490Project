import ssl
import threading
from time import sleep

from DiffHellman.DHclient import DHClient
from DiffHellman.DHserver import DHServer

HOST = '127.0.0.1'
PORT = 5001


def main():
    # Port and hostname that the SSL server will be running on
    host = 'localhost'
    port = 5001

    th = threading.Thread(target=run_server)
    th.start()
    sleep(1)        # ENSURE SERVER IS RUNNING FIRST
    # Start the client
    # ssl.PROTOCOL_TLS_CLIENT AUTO NEGOTIATES. MAY WANT TO HARD CODE FLAGS FOR TESTING
    client = DHClient(host, port, DHClient.AUTHENTICATED)
    # TEST
    client.connect()
    # END HERE
    # Now transfer a file across this connection
    client.receive_file()

    th.join()


def run_server():
    # Start the server
    server = DHServer(HOST, PORT, DHServer.AUTHENTICATED)
    server.start_server()
    server.send_file('./SSL/util/frankenstein_book.txt')


if __name__ == "__main__":
    main()
