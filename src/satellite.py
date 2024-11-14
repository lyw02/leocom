import signal
import socket
from utils.simulation.satellite_emulator import SatelliteEmulator
from utils.simulation.satellite_network import SatelliteNetwork

ground_host = "127.0.0.1"
ground_port = 7111

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as gs:
    gs.connect((ground_host, int(ground_port)))
    satellite = SatelliteEmulator("Satellite-01", "127.0.0.1", "5000", ground_host, ground_port, gs)
    satellite.register_to_network("127.0.0.1", "5678")
    satellite.get_satellites_list()
    
    print(f"[Satellite] Connected to Ground Station at {ground_host}:{ground_port}")
    satellite.listen_for_data()

def signal_handler(signal, frame):
    print("[Satellite Network] Shutting down all satellites...")
    # for satellite in satellite_network.satellites:
    #     satellite.shutdown()

signal.signal(signal.SIGINT, signal_handler)
