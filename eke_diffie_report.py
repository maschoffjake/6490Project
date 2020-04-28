import threading
from time import sleep
import struct
import os
from Crypto.Random import get_random_bytes
from EKE.DHClient import EKEDiffieClient
from EKE.DHServer import EKEDiffieServer

received = 1

def main():
    host = "localhost"
    port = 5002
    password = get_random_bytes(16)

    server = EKEDiffieServer(host, port)
    server.add_password("Alice", password)
    client = EKEDiffieClient(host, port, password)
    th = threading.Thread(target=run_server, args=[server,])
    th.start()
    sleep(0.05)
    print("CLIENT: Connecting")
    client.connect()

    print("CLIENT: Sending public key")
    client.send_public_key()

    print("CLIENT: Waiting for public key")
    client.receive_public_key()

    client.receive_file()


    print(client.secret_key)
    print(server.secret_key)
    return

def run_server(server):
    print("SERVER: Starting server")
    server.start_server()

    print("SERVER: Waiting for public key")
    server.receive_public_key()

    print("SERVER: Sending public key")
    server.send_public_key()

    server.send_file('./SSL/util/frankenstein_book.txt')
    return

if __name__ == "__main__":
    main()

