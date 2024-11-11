import signal
import threading
from utils.simulation.satellite_emulator import SatelliteEmulator
from utils.simulation.satellite_network import SatelliteNetwork


satellite1 = SatelliteEmulator("127.0.0.1", "5000")
satellite2 = SatelliteEmulator("127.0.0.1", "5001")

satellite_network = SatelliteNetwork([satellite1, satellite2])

def signal_handler(signal, frame):
    print("[Satellite Network] Shutting down all satellites...")
    for satellite in satellite_network.satellites:
        satellite.shutdown()

signal.signal(signal.SIGINT, signal_handler)

for satellite in satellite_network.satellites:
    threading.Thread(target=satellite.listen_for_data, daemon=True).start()

# Start the data routing and handover simulation
satellite_network.start_data_routing()
