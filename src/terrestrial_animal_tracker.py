import random
from utils.simulation.wildlife_tracker import WildLifeTracker


class TerrestrialAnimalTracker(WildLifeTracker):

    def __init__(
        self,
        device_name,
        heart_rate_range=(20, 90),
        body_temperature_range=(36.0, 39.0),
    ):
        super().__init__(
            device_name,
            heart_rate_range,
            body_temperature_range,
        )
        self.height = None
        self.depth = None
    def collect_data(self):
       
        data = super().collect_data()
                
        self.message_queue.put(data)

        return data


name = "TerrestrialAnimalTrackerDevice" + str(random.randint(1, 1000))
tracker = TerrestrialAnimalTracker(name)
tracker.run()
