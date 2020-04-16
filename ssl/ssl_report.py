from ssl_server import ssl_server
from ssl_client import ssl_client

# Port and hostname that the SSL server will be running on
HOST = 'localhost'
PORT = 5001


def main():

    # Start the server
    server = ssl_server(HOST, PORT)
    server.start_server()

    # Start the client
    client = ssl_client(HOST, PORT)
    client.connect()

    # Now transfer a file across this connection
    # client.receive_file()
    server.send_file('./util/frankenstein_book.txt')

if __name__ == "__main__":
    main()