import ssl
import threading
import pyRAPL
import numpy as np
from time import sleep

# Oauth class
from oauth2.Oauth import Oauth2

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
    # You must first authenticate the client with a signin
    client = Oauth2()

    # Power measurement, and number of times to repeat
    devices_to_record = [pyRAPL.Device.PKG, pyRAPL.Device.DRAM]
    repeat = 500
    for device in devices_to_record:
        if device == pyRAPL.Device.PKG:
            print("Measuring PKG...")
        else:
            print("Measuring DRAM...")
        for i in range(repeat):
            # Start the client
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


if __name__ == "__main__":
    main()
