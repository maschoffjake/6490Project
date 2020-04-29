import threading
import time
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

TIME = {
    'client_connect_time': [],
    'client_receive_time': [],
    'server_connect_time': [],
    'server_send_time': []
}

HOST = '127.0.0.1'
PORT = 5002


def main():
    host = "localhost"
    port = 5002
    password = get_random_bytes(16)
    devices_to_record = [pyRAPL.Device.PKG, pyRAPL.Device.DRAM, "time"]
    repeat = 10

    for device in devices_to_record:
        if device == pyRAPL.Device.PKG:
            print("Measuring PKG...")
        elif device == pyRAPL.Device.DRAM:
            print("Measuring DRAM...")
        elif device == "time":
            print("Measuring Time...")
        else:
            print("Unknown device.")
            return
        for i in range(repeat):
            th = threading.Thread(target=run_server, args=[device, password])
            th.start()
            sleep(0.05)

            # Start the client
            client = EKEDiffieClient(host, port, password)

            meter_client_connect = 0
            connect_start = 0
            connect_end = 0
            if device != "time":
                pyRAPL.setup(devices=[device])
                meter_client_connect = pyRAPL.Measurement('client_connect')
                meter_client_connect.begin()
            else:
                connect_start = time.time()
            # print("CLIENT: Connecting")
            client.connect()

            # print("CLIENT: Sending public key")
            client.send_public_key()

            # print("CLIENT: Waiting for public key")
            client.receive_public_key()

            if device != "time":
                meter_client_connect.end()
            else:
                connect_end = time.time()

            # Now transfer a file across this connection
            meter_client_receive = pyRAPL.Measurement('client_receive')
            receive_start = 0
            receive_end = 0
            if device != "time":
                meter_client_receive.begin()
            else:
                receive_start = time.time()

            client.receive_file()

            if device != "time":
                meter_client_receive.end()
            else:
                receive_end = time.time()

            if device == pyRAPL.Device.PKG:
                ENERGY_USED['client_connect_pkg'] += meter_client_connect.result.pkg
                ENERGY_USED['client_receive_pkg'] += meter_client_receive.result.pkg
            elif device == pyRAPL.Device.DRAM:
                ENERGY_USED['client_connect_dram'] += meter_client_connect.result.dram
                ENERGY_USED['client_receive_dram'] += meter_client_receive.result.dram
            elif device == "time":
                TIME['client_connect_time'] += [connect_end - connect_start]
                TIME['client_receive_time'] += [receive_end - receive_start]

            th.join()
        print("Done.\n")
    print_energy_used()
    return


def print_energy_used():
    print("CPU Energy Uses")
    print("Client Connect: ", np.average(ENERGY_USED['client_connect_pkg']) / 1000, 'mJ')
    print("Client Receiving File: ", np.average(ENERGY_USED['client_receive_pkg']) / 1000, 'mJ')
    print("Server Connect: ", np.average(ENERGY_USED['server_connect_pkg']) / 1000, 'mJ')
    print("Server Sending File: ", np.average(ENERGY_USED['server_send_pkg']) / 1000, 'mJ')
    print()
    print("DRAM Energy Uses")
    print("Client Connect: ", np.average(ENERGY_USED['client_connect_dram']) / 1000, 'mJ')
    print("Client Receiving File: ", np.average(ENERGY_USED['client_receive_dram']) / 1000, 'mJ')
    print("Server Connect: ", np.average(ENERGY_USED['server_connect_dram']) / 1000, 'mJ')
    print("Server Sending File: ", np.average(ENERGY_USED['server_send_dram']) / 1000, 'mJ')
    print()
    print("Time")
    print("Client Connect: ", np.average(TIME['client_connect_time']), 'S')
    print("Client Receiving File: ", np.average(TIME['client_receive_time']), 'S')
    print("Server Connect: ", np.average(TIME['server_connect_time']), 'S')
    print("Server Sending File: ", np.average(TIME['server_send_time']), 'S')


def run_server(device, password):
    # Start the server
    server = EKEDiffieServer(HOST, PORT)
    server.add_password("Alice", password)

    meter_server_connect = 0
    connect_start = 0
    connect_end = 0
    if device != "time":
        pyRAPL.setup(devices=[device])
        meter_server_connect = pyRAPL.Measurement('server_connect')
        meter_server_connect.begin()
    else:
        connect_start = time.time()
    # print("SERVER: Starting server")
    server.start_server()

    # print("SERVER: Waiting for public key")
    server.receive_public_key()

    # print("SERVER: Sending public key")
    server.send_public_key()

    if device != "time":
        meter_server_connect.end()
    else:
        connect_end = time.time()

    # Send file
    meter_server_send = pyRAPL.Measurement('server_send')
    send_start = 0
    send_end = 0
    if device != "time":
        meter_server_send.begin()
    else:
        send_start = time.time()

    server.send_file('./SSL/util/frankenstein_book.txt')

    if device != "time":
        meter_server_send.end()
    else:
        send_end = time.time()

    if device == pyRAPL.Device.PKG:
        ENERGY_USED['server_connect_pkg'] += meter_server_connect.result.pkg
        ENERGY_USED['server_send_pkg'] += meter_server_send.result.pkg
    elif device == pyRAPL.Device.DRAM:
        ENERGY_USED['server_connect_dram'] += meter_server_connect.result.dram
        ENERGY_USED['server_send_dram'] += meter_server_send.result.dram
    elif device == "time":
        TIME['server_connect_time'] += [connect_end - connect_start]
        TIME['server_send_time'] += [send_end - send_start]
    return


if __name__ == "__main__":
    main()

