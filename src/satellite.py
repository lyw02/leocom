import signal
import threading
import socket
from utils.simulation.satellite_emulator import SatelliteEmulator
from utils.simulation.satellite_network import SatelliteNetwork


satellite1 = SatelliteEmulator("127.0.0.1", "5000")
satellite2 = SatelliteEmulator("127.0.0.1", "5001")
ground_host = "127.0.0.1"
ground_port = 5111

satellite_network = SatelliteNetwork([satellite1, satellite2])

def signal_handler(signal, frame):
    print("[Satellite Network] Shutting down all satellites...")
    for satellite in satellite_network.satellites:
        satellite.shutdown()

signal.signal(signal.SIGINT, signal_handler)

for satellite in satellite_network.satellites:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as gs:
        gs.connect((ground_host, int(ground_port)))
        print(f"[Satellite] Connected to Ground Station at {ground_host}:{ground_port}")
        threading.Thread(target=satellite.listen_for_data, args=(gs), daemon=True).start()

# Start the data routing and handover simulation
satellite_network.start_data_routing()
