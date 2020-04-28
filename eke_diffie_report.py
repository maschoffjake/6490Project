import threading
from time import sleep
import struct
import os
import pyRAPL
import numpy as np
from Crypto.Random import get_random_bytes
from EKE.DHClient import EKEDiffieClient
from EKE.DHServer import EKEDiffieServer

ENERGY_USED = {
    'client_connect_pkg': [],
    'client_receive_pkg': [],
    'server_connect_pkg': [],
    'server_send_pkg': [],
    'client_connect_dram': [],
    'client_receive_dram': [],
    'server_connect_dram': [],
    'server_send_dram': []
}

HOST = '127.0.0.1'
PORT = 5002

def main():
    host = "localhost"
    port = 5002
    password = get_random_bytes(16)
    devices_to_record = [pyRAPL.Device.PKG, pyRAPL.Device.DRAM]
    repeat = 500

    for device in devices_to_record:
        if device == pyRAPL.Device.PKG:
            print("Measuring PKG...")
        else:
            print("Measuring DRAM...")
        for i in range(repeat):
            th = threading.Thread(target=run_server, args=[device,password,])
            th.start()
            sleep(0.05)

            # Start the client
            client = EKEDiffieClient(host, port, password)
            pyRAPL.setup(devices=[device])
            meter_client_connect = pyRAPL.Measurement('client_connect')
            meter_client_connect.begin()
            print("CLIENT: Connecting")
            client.connect()

            print("CLIENT: Sending public key")
            client.send_public_key()

            print("CLIENT: Waiting for public key")
            client.receive_public_key()
            meter_client_connect.end()

            # Now transfer a file across this connection
            meter_client_receive = pyRAPL.Measurement('client_receive')
            meter_client_receive.begin()
            client.receive_file()
            meter_client_receive.end()

            if device == pyRAPL.Device.PKG:
                ENERGY_USED['client_connect_pkg'] += meter_client_connect.result.pkg
                ENERGY_USED['client_receive_pkg'] += meter_client_receive.result.pkg
            else:
                ENERGY_USED['client_connect_dram'] += meter_client_connect.result.dram
                ENERGY_USED['client_receive_dram'] += meter_client_receive.result.dram

                th.join()
        print("Done.\n")
    print_energy_used()
    return


def print_energy_used():
    print("CPU Energy Uses")
    print("Client Connect: ", np.average(ENERGY_USED['client_connect_pkg']), '\u03BCJ')
    print("Client Receiving File: ", np.average(ENERGY_USED['client_receive_pkg']), '\u03BCJ')
    print("Server Connect: ", np.average(ENERGY_USED['server_connect_pkg']), '\u03BCJ')
    print("Server Sending File: ", np.average(ENERGY_USED['server_send_pkg']), '\u03BCJ')
    print()
    print("DRAM Energy Uses")
    print("Client Connect: ", np.average(ENERGY_USED['client_connect_dram']), '\u03BCJ')
    print("Client Receiving File: ", np.average(ENERGY_USED['client_receive_dram']), '\u03BCJ')
    print("Server Connect: ", np.average(ENERGY_USED['server_connect_dram']), '\u03BCJ')
    print("Server Sending File: ", np.average(ENERGY_USED['server_send_dram']), '\u03BCJ')


def run_server(device, password):

        # Start the server
    server = EKEDiffieServer(HOST, PORT)
    server.add_password("Alice", password)
    pyRAPL.setup(devices=[device])
    meter_server_connect = pyRAPL.Measurement('server_connect')
    meter_server_connect.begin()
    print("SERVER: Starting server")
    server.start_server()

    print("SERVER: Waiting for public key")
    server.receive_public_key()

    print("SERVER: Sending public key")
    server.send_public_key()
    meter_server_connect.end()

    # Send file
    meter_server_send = pyRAPL.Measurement('server_send')
    meter_server_send.begin()
    server.send_file('./SSL/util/frankenstein_book.txt')
    meter_server_send.end()

    if device == pyRAPL.Device.PKG:
        ENERGY_USED['server_connect_pkg'] += meter_server_connect.result.pkg
        ENERGY_USED['server_send_pkg'] += meter_server_send.result.pkg
    else:
        ENERGY_USED['server_connect_dram'] += meter_server_connect.result.dram
        ENERGY_USED['server_send_dram'] += meter_server_send.result.dram


    return

if __name__ == "__main__":
    main()

