import signal
from utils.simulation import SatelliteEmulator

def signal_handler(signal, frame):
    global satellite
    satellite.shutdown()

signal.signal(signal.SIGINT, signal_handler)

satellite = SatelliteEmulator("127.0.0.1", "5000")
satellite.listen_for_data()
