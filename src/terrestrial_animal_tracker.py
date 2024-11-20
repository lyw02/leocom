import random
from utils.simulation.wildlife_tracker import WildLifeTracker

#imports WildLifeTracker which controls all trackers
class TerrestrialAnimalTracker(WildLifeTracker):

    def __init__(
        self,
        device_name,
        source_ip,
        source_port,
        heart_rate_range=(20, 90),
        body_temperature_range=(36.0, 39.0),
    ):
        super().__init__(
            device_name,
            source_ip,
            source_port,
            heart_rate_range,
            body_temperature_range,
        )
        self.height = None
        self.depth = None
    def collect_data(self):
       
        data = super().collect_data()
                
        self.message_queue.put(data)

        return data


'''name = "TerrestrialAnimalTrackerDevice" + str(random.randint(1, 1000))
tracker = TerrestrialAnimalTracker(name)
tracker.run()'''
def main(host, port):
    name = "TerrestrialAnimalTrackerDevice" + str(random.randint(1, 1000))
    tracker = TerrestrialAnimalTracker(name, host, port)
    tracker.run()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Emulate a Terrestrial Animal tracker")
    parser.add_argument('--host', type=str, help="Animal Tracker IP address")
    parser.add_argument('--port', type=str, help="Animal Tracker port")
    args = parser.parse_args()

    if args.host is None:
        print("Please specify the IP Address of the Animal Tracker")
        exit(1)
    if args.port is None:
        print("Please specify the Animal Tracker port")
        exit(1)

    main(args.host, args.port)
