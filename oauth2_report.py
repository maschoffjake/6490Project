import ssl
import threading
import numpy as np
import time

# Oauth class
from oauth2.Oauth import Oauth2

# Resource measurement libs
import tracemalloc
import pyRAPL
import psutil
import multiprocessing as mp

ENERGY_USED = {
    'client_connect_pkg': [],
    'client_receive_pkg': [],
    'client_connect_dram': [],
    'client_receive_dram': []
}

TIME = {
    'client_connect_time': [],
    'client_receive_time': []
}

number_of_power_test_iterations = 500
number_of_memory_test_iterations = 1
number_of_cpu_test_iterations = 20
number_of_time_test_iterations = 500

def main():
    # You must first authenticate the client with a signin
    client = Oauth2()

    # Run power tests, memory tests, and then CPU tests
    # run_power_tests(client=client)
    # run_memory_tests(client=client)
    # client.connect()    # Run a connect before to ensure creds is populated for cpu utilization tests
    # run_cpu_utilization_tests(client=client)
    run_time_tests(client)


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
    cpu_percents_connect = []
    cpu_percents_receive_file = []
    for i in range(number_of_cpu_test_iterations):

        # Measure connect cpu %
        worker_process = mp.Process(target=run_connect, args=(client,))
        worker_process.start()
        p = psutil.Process(worker_process.pid)

        # Log CPU usage every 10ms
        while worker_process.is_alive():
            try:
                cpu_percents_connect.append(p.cpu_percent())
            except Exception as e:
                print(str(e))
            time.sleep(0.01)

        worker_process.join()

        # Measure connect cpu %
        worker_process = mp.Process(target=run_receive_file, args=(client,))
        worker_process.start()
        p = psutil.Process(worker_process.pid)

        # Log CPU usage every 10ms
        while worker_process.is_alive():
            try:
                cpu_percents_receive_file.append(p.cpu_percent())
            except Exception as e:
                print(str(e))
            time.sleep(0.01)

        worker_process.join()

    print("Average CPU usage over", number_of_cpu_test_iterations, "tests for connecting:", "%.4f" % (np.average(cpu_percents_connect)/psutil.cpu_count()))
    print("Average CPU usage over", number_of_cpu_test_iterations, "tests for receiving file:", "%.4f" % (np.average(cpu_percents_receive_file)/psutil.cpu_count()))
    print()
    print("Max CPU usage over", number_of_cpu_test_iterations, "tests for connecting:", "%.4f" % (max(cpu_percents_connect)/psutil.cpu_count()))
    print("Max CPU usage over", number_of_cpu_test_iterations, "tests for receiving file:", "%.4f" % (max(cpu_percents_receive_file)/psutil.cpu_count()))


def run_connect(client):
    """
        Threaded function for recording the CPU usage for connecting for the client
    """
    client.connect()

def run_receive_file(client):
    """
        Threaded function for recording the CPU usage for receiving a file from the client
    """
    client.receive_file()

def run_time_tests(client):
    '''
        Function used for timing the connect and receive file methods of OAuth2
    '''
    for i in range(number_of_time_test_iterations):
        # Time how long it takes to connect
        connect_start = time.time()
        client.connect()
        connect_end = time.time()

        # Time how long it takes to receive a file
        receive_start = time.time()
        client.receive_file()
        receive_end = time.time()
        TIME['client_connect_time'] += [connect_end - connect_start]
        TIME['client_receive_time'] += [receive_end - receive_start]
    print_time_used()   

def print_time_used():
    print("Time")
    print("Client Connect: ", np.average(TIME['client_connect_time']), 'S')
    print("Client Receiving File: ", np.average(TIME['client_receive_time']), 'S')

def print_energy_used():
    print("CPU Energy Uses")
    print("Client Connect: ", np.average(ENERGY_USED['client_connect_pkg']), '\u03BCJ')
    print("Client Receiving File: ", np.average(ENERGY_USED['client_receive_pkg']), '\u03BCJ')
    print()
    print("DRAM Energy Uses")
    print("Client Connect: ", np.average(ENERGY_USED['client_connect_dram']), '\u03BCJ')
    print("Client Receiving File: ", np.average(ENERGY_USED['client_receive_dram']), '\u03BCJ')


if __name__ == "__main__":
    main()
