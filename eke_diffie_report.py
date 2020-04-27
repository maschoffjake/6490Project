import threading
from time import sleep
from EKE.DHClient import EKEDiffieClient
from EKE.DHServer import EKEDiffieServer

received = 1

def main():
    host = "localhost"
    port = 5002

    server = EKEDiffieServer(host, port)
    client = EKEDiffieClient(host, port, "password")
    th = threading.Thread(target=run_server, args=[server,])
    th.start()
    sleep(0.05)
    print("CLIENT: Connecting")
    client.connect()

    print("CLIENT: Sending public key")
    client.send_public_key()

    print("CLIENT: Waiting for public key")
    client.receive_public_key()


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
    return


if __name__ == "__main__":
    main()