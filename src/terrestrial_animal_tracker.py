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


tracker = TerrestrialAnimalTracker(
    "TerrestrialAnimalTrackerDevice"
)
tracker.run()
