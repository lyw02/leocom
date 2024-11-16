import random
from utils.simulation.wildlife_tracker import WildLifeTracker


class BirdTracker(WildLifeTracker):

    def __init__(
        self,
        device_name,
        heart_rate_range=(100, 600),
        body_temperature_range=(39.0, 43.0),
    ):
        super().__init__(
            device_name,
            heart_rate_range,
            body_temperature_range,
        )
        self.height = random.uniform(0, 9000)

    def collect_data(self):
        self.height += random.uniform(-5, 5)
        self.height = max(0, min(11000, self.height))

        data = super().collect_data()
        data.update(height=self.height)
        
        self.message_queue.put(data)

        return data


tracker = BirdTracker("BirdTrackerDevice")
tracker.run()
