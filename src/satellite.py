import signal
import socket

from utils.simulation.satellite_emulator import SatelliteEmulator
from ip_config import ground_station_host, ground_station_port, registration_server_host, registration_server_port


def main(name, host, port):
    print([ground_station_host, ground_station_port])
    satellite = SatelliteEmulator(name, host, port, ground_station_host, ground_station_port)
    satellite.register_to_network(registration_server_host, registration_server_port)
    satellite.get_satellites_list()
    
    satellite.listen_for_data()

# def signal_handler(signal, frame):
#     print("[Satellite Network] Shutting down all satellites...")
#     # for satellite in satellite_network.satellites:
#     #     satellite.shutdown()

# signal.signal(signal.SIGINT, signal_handler)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Emulate a satellite")
    parser.add_argument('--name', type=str, help="The name of the satellite")
    parser.add_argument('--host', type=str, help="Satellite IP address")
    parser.add_argument('--port', type=str, help="Satellite port")
    args = parser.parse_args()

    if args.name is None:
        print("Please specify the Satellite Name")
        exit(1)
    if args.host is None:
        print("Please specify the IP Address of the Satellite")
        exit(1)
    if args.port is None:
        print("Please specify the Satellite port")
        exit(1)

    # satellite = SatelliteEmulator(args.name, args.host, args.port)
    # satellite.listen_for_data()
    main(args.name, args.host, args.port)
