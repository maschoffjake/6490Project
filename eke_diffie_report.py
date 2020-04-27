import threading
from time import sleep
from DiffieHellman.DiffieClient import DiffieClient
from DiffieHellman.DiffieServer import DiffieServer


def main():
    host = "localhost"
    port = 5002

    server = DiffieServer(host, port)
    client = DiffieClient(host, port)
    th = threading.Thread(target=run_server, args=[server,])
    th.start()
    sleep(0.05)
    print("Client Connecting")
    client.connect()

    print("Client sending public key")
    client.send_public_key()

    print("Client waiting for public key")
    client.receive_public_key()


    print(client.secret_key)
    print(server.secret_key)
    return

def run_server(server):
    print("Starting Server")
    server.start_server()

    
    print("Server waiting for public key")
    server.receive_public_key()

    print("Server sending public key")
    server.send_public_key()
    return


if __name__ == "__main__":
    main()
