import signal
import threading

from demo_utils.simulation.satellite_emulator import SatelliteEmulator


satellite = SatelliteEmulator("127.0.0.1", "9000")
stop_event = threading.Event()


def signal_handler(signal, frame):
    print("[Satellite Network] Shutting down satellite...")
    satellite.shutdown()


signal.signal(signal.SIGINT, signal_handler)

threading.Thread(target=satellite.listen_for_data, daemon=True).start()

stop_event.wait()
