from utils.simulation import WildLifeTracker


class TerrestrialAnimalTracker(WildLifeTracker):

    def __init__(
        self,
        device_name,
        satellite_host,
        satellite_port,
        heart_rate_range=(20, 90),
        body_temperature_range=(36.0, 39.0),
    ):
        super().__init__(
            device_name,
            satellite_host,
            satellite_port,
            heart_rate_range,
            body_temperature_range,
        )


tracker = TerrestrialAnimalTracker(
    "TerrestrialAnimalTrackerDivice", "127.0.0.1", "5000"
)
tracker.run()
