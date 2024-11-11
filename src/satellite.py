from utils.simulation import SatelliteEmulator


satellite = SatelliteEmulator("127.0.0.1", "5000")
satellite.listen_for_data()
