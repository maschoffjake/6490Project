import ssl
import threading
import pyRAPL
import numpy as np

from SSL.CertClient import CertClient
from SSL.CertServer import CertServer
from time import sleep

HOST = '127.0.0.1'
PORT = 5001

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


def main():
    # Port and hostname that the SSL server will be running on
    host = 'localhost'
    port = 5001

    devices_to_record = [pyRAPL.Device.PKG, pyRAPL.Device.DRAM]
    repeat = 500
    for device in devices_to_record:
        if device == pyRAPL.Device.PKG:
            print("Measuring PKG...")
        else:
            print("Measuring DRAM...")
        for i in range(repeat):
            th = threading.Thread(target=run_server, args=[device,])
            th.start()
            sleep(0.05)

            # Start the client
            client = CertClient(host, port, ssl.PROTOCOL_TLS_CLIENT)
            pyRAPL.setup(devices=[device])
            meter_client_connect = pyRAPL.Measurement('client_connect')
            meter_client_connect.begin()
            client.connect()
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


def run_server(device):
    # Start the server
    server = CertServer(HOST, PORT, ssl.PROTOCOL_TLS_SERVER)
    pyRAPL.setup(devices=[device])
    meter_server_connect = pyRAPL.Measurement('server_connect')
    meter_server_connect.begin()
    server.start_server()
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


if __name__ == "__main__":
    main()
