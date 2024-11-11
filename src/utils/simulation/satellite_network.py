import time
import random


class SatelliteNetwork:
    def __init__(self, satellites):
        self.satellites = satellites  # List of SatelliteEmulator instances
        self.current_satellite_index = 0

    def perform_handover(self):
        # Handover to the next satellite in network
        self.current_satellite_index = (self.current_satellite_index + 1) % len(
            self.satellites
        )
        current_satellite = self.satellites[self.current_satellite_index]
        print(
            f"Handover to Satellite {current_satellite.host}:{current_satellite.port}"
        )

    def start_data_routing(self):
        # Start data routing and handover simulation
        while True:
            current_satellite = self.satellites[self.current_satellite_index]
            print(
                f"Routing data through Satellite {current_satellite.host}:{current_satellite.port}"
            )

            # Simulate data reception and processing delay
            time.sleep(2)

            # Trigger handover at random intervals to simulate network conditions
            if random.random() < 0.2:  # 20% chance of handover
                self.perform_handover()
