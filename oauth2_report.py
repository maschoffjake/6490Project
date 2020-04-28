import ssl
import threading
import pyRAPL
import numpy as np
from time import sleep

# Oauth class
from oauth2.Oauth import Oauth2

# Memory library
import tracemalloc

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

number_of_power_test_iterations = 500
number_of_memory_test_iterations = 1
number_of_cpu_test_iterations = 1

def main():
    # You must first authenticate the client with a signin
    client = Oauth2()

    # Run power tests, memory tests, and then CPU tests
    # run_power_tests(client=client)
    run_memory_tests(client=client)
    # run_cpu_utilization_tests(client=client)



def run_power_tests(client):
    '''
        Run the power tests for Oauth2 (DRAM and PKG)
        Measuring both connection (using refresh tokens) and
        downloading a file from google drive
    '''
    # Power measurement, and number of times to repeat
    devices_to_record = [pyRAPL.Device.PKG, pyRAPL.Device.DRAM]
    for device in devices_to_record:
        if device == pyRAPL.Device.PKG:
            print("Measuring PKG...")
        else:
            print("Measuring DRAM...")
        for i in range(number_of_power_test_iterations):
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

def run_memory_tests(client):
    '''
        Run memory tests to see how much memory is consumed by Oauth2
        Measuring both connection (using refresh tokens) and
        downloading a file from google drive
    '''
    total_peak_memory_connect = 0
    total_peak_memory_receive_file = 0
    for i in range(number_of_memory_test_iterations):

        # Measure connection memory
        tracemalloc.start()
        client.connect()
        _, peak = tracemalloc.get_traced_memory()
        total_peak_memory_connect += peak

        # Measure connection memory
        tracemalloc.start()
        client.receive_file()
        _, peak = tracemalloc.get_traced_memory()
        total_peak_memory_receive_file += peak

    # Compute average in MB 
    average_connection_memory_MB = (total_peak_memory_connect/number_of_memory_test_iterations) / 10**6
    average_receive_memory_MB = (total_peak_memory_receive_file/number_of_memory_test_iterations) / 10**6
    print("Average memory consumption over", number_of_memory_test_iterations, "tests for connecting:", "%.4f" % average_connection_memory_MB, "MB")
    print("Average memory consumption over", number_of_memory_test_iterations, "tests for receiving file:", "%.4f" % average_receive_memory_MB, "MB")


def run_cpu_utilization_tests(client):
    '''
        Run CPU tests to see how much CPU is utilized by Oauth2
        Measuring both connection (using refresh tokens) and
        downloading a file from google drive
    '''
    pass

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
