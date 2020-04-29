import ssl
import threading
import time
import tracemalloc

import psutil
import pyRAPL
import numpy as np
import multiprocessing as mp

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

TIME = {
    'client_connect_time': [],
    'client_receive_time': [],
    'server_connect_time': [],
    'server_send_time': []
}

number_of_memory_test_iterations = 10
number_of_cpu_test_iterations = 100

SSL_PROTOCOL_CLIENT = ssl.PROTOCOL_TLS_CLIENT
SSL_PROTOCOL_SERVER = ssl.PROTOCOL_TLS_SERVER


def main():
    protocols = ['TLS', ssl.PROTOCOL_SSLv2]
    for protocol in protocols:
        global SSL_PROTOCOL_CLIENT
        global SSL_PROTOCOL_SERVER
        if protocol == "TLS":
            SSL_PROTOCOL_CLIENT = ssl.PROTOCOL_TLS_CLIENT
            SSL_PROTOCOL_SERVER = ssl.PROTOCOL_TLS_SERVER
        else:
            SSL_PROTOCOL_CLIENT = protocol
            SSL_PROTOCOL_SERVER = protocol
        # run_memory_tests()
        # run_cpu_utilization_tests()
        power_time()


def power_time():
    print(SSL_PROTOCOL_SERVER)
    devices_to_record = [pyRAPL.Device.PKG, pyRAPL.Device.DRAM, "time"]
    repeat = 500
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
            th = threading.Thread(target=run_server, args=[device,])
            th.start()
            sleep(0.05)

            # Start the client
            client = CertClient(HOST, PORT, SSL_PROTOCOL_CLIENT)

            meter_client_connect = 0
            connect_start = 0
            connect_end = 0
            if device != "time":
                pyRAPL.setup(devices=[device])
                meter_client_connect = pyRAPL.Measurement('client_connect')
                meter_client_connect.begin()
            else:
                connect_start = time.time()

            client.connect()

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
    print()
    print("Time")
    print("Client Connect: ", np.average(TIME['client_connect_time']), 'S')
    print("Client Receiving File: ", np.average(TIME['client_receive_time']), 'S')
    print("Server Connect: ", np.average(TIME['server_connect_time']), 'S')
    print("Server Sending File: ", np.average(TIME['server_send_time']), 'S')


def run_server(device):
    # Start the server
    server = CertServer(HOST, PORT, SSL_PROTOCOL_SERVER)

    meter_server_connect = 0
    connect_start = 0
    connect_end = 0
    if device != "time":
        pyRAPL.setup(devices=[device])
        meter_server_connect = pyRAPL.Measurement('server_connect')
        meter_server_connect.begin()
    else:
        connect_start = time.time()

    server.start_server()

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


def run_memory_tests():
    '''
        Run memory tests to see how much memory is consumed by Oauth2
        Measuring both connection (using refresh tokens) and
        downloading a file from google drive
    '''
    print("Running memory test...")
    client = CertClient(HOST, PORT, SSL_PROTOCOL_CLIENT)
    total_peak_memory_connect = 0
    total_peak_memory_receive_file = 0
    for i in range(number_of_memory_test_iterations):
        th = threading.Thread(target=run_memory_tests_server)
        th.start()
        sleep(0.05)
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

        th.join()

    # Compute average in MB
    average_connection_memory_MB = (total_peak_memory_connect / number_of_memory_test_iterations) / 10 ** 6
    average_receive_memory_MB = (total_peak_memory_receive_file / number_of_memory_test_iterations) / 10 ** 6
    print("[Client] Average memory consumption over", number_of_memory_test_iterations, "tests for connecting:",
          "%.4f" % average_connection_memory_MB, "MB")
    print("[Client] Average memory consumption over", number_of_memory_test_iterations, "tests for receiving file:",
          "%.4f" % average_receive_memory_MB, "MB")


def run_memory_tests_server():
    server = CertServer(HOST, PORT, SSL_PROTOCOL_SERVER)
    total_peak_memory_connect = 0
    total_peak_memory_receive_file = 0
    # Measure connection memory
    tracemalloc.start()
    server.start_server()
    _, peak = tracemalloc.get_traced_memory()
    total_peak_memory_connect += peak

    # Measure connection memory
    tracemalloc.start()
    server.send_file('./SSL/util/frankenstein_book.txt')
    _, peak = tracemalloc.get_traced_memory()
    total_peak_memory_receive_file += peak
    average_connection_memory_MB = (total_peak_memory_connect / number_of_memory_test_iterations) / 10 ** 6
    average_receive_memory_MB = (total_peak_memory_receive_file / number_of_memory_test_iterations) / 10 ** 6
    print("[Server] Average memory consumption over", number_of_memory_test_iterations, "tests for connecting:",
          "%.4f" % average_connection_memory_MB, "MB")
    print("[Server] Average memory consumption over", number_of_memory_test_iterations, "tests for sending file:",
          "%.4f" % average_receive_memory_MB, "MB")


def run_cpu_utilization_tests():
    '''
        Run CPU tests to see how much CPU is utilized by Oauth2
        Measuring both connection (using refresh tokens) and
        downloading a file from google drive
    '''
    print("Running CPU Utilization test...")
    cpu_percents = []
    for i in range(number_of_cpu_test_iterations):

        # Measure connect cpu %
        worker_process = mp.Process(target=run_client_cpu_util)
        worker_process.start()
        p = psutil.Process(worker_process.pid)

        # Log CPU usage every 10ms
        while worker_process.is_alive():
            try:
                cpu_percents.append(p.cpu_percent())
            except Exception as e:
                print(str(e))
            time.sleep(0.01)

        worker_process.join()

    print("Average CPU usage over", number_of_cpu_test_iterations, "tests between server and client connection:",
          "%.4f" % (np.average(cpu_percents) / psutil.cpu_count()))
    print("Max CPU usage over", number_of_cpu_test_iterations, "tests between server and client connection:",
          "%.4f" % (max(cpu_percents) / psutil.cpu_count()))


def run_client_cpu_util():
    th = threading.Thread(target=run_server_cpu_util)
    th.start()
    sleep(0.05)

    # Start the client
    client = CertClient(HOST, PORT, SSL_PROTOCOL_CLIENT)
    client.connect()
    client.receive_file()

    th.join()


def run_server_cpu_util():
    server = CertServer(HOST, PORT, SSL_PROTOCOL_SERVER)
    server.start_server()
    server.send_file('./SSL/util/frankenstein_book.txt')


if __name__ == "__main__":
    main()
