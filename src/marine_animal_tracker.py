import random
from utils.simulation.wildlife_tracker import WildLifeTracker


class MarineAnimalTracker(WildLifeTracker):

    def __init__(
        self,
        device_name,
        heart_rate_range=(20, 40),
        body_temperature_range=(36.0, 39.0),
    ):
        super().__init__(
            device_name,
            heart_rate_range,
            body_temperature_range,
        )
        self.depth = random.uniform(0, 11000)

    def collect_data(self, source_ip, source_port):
        self.depth += random.uniform(-1, 1)
        self.depth = max(0, min(11000, self.depth))

        data = super().collect_data(source_ip, source_port)
        data.update(depth=self.depth)

        return data


tracker = MarineAnimalTracker("MarineAnimalTrackerDevice")
tracker.run()
