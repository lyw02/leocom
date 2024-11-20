import random
from utils.simulation.wildlife_tracker import WildLifeTracker

#imports WildLifeTracker which controls all trackers
class MarineAnimalTracker(WildLifeTracker):

    def __init__(
        self,
        device_name,
        source_ip,
        source_port,
        heart_rate_range=(20, 40),
        body_temperature_range=(36.0, 39.0),
    ):
        super().__init__(
            device_name,
            source_ip,
            source_port,
            heart_rate_range,
            body_temperature_range,
        )
        self.depth = random.uniform(0, 11000)
        self.height = None

    def collect_data(self):
        self.depth += random.uniform(-1, 1)
        self.depth = max(0, min(11000, self.depth))

        data = super().collect_data()
        data.update(depth=self.depth)
        self.message_queue.put(data)

        return data

'''name = "MarineAnimalTrackerDevice" + str(random.randint(1, 1000))
tracker = MarineAnimalTracker(name)
tracker.run()'''

def main(host, port):
    name = "MarineAnimalTrackerDevice" + str(random.randint(1, 1000))
    tracker = MarineAnimalTracker(name, host, port)
    tracker.run()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Emulate a Marine Animal tracker")
    parser.add_argument('--host', type=str, help="Marine Animal Tracker IP address")
    parser.add_argument('--port', type=str, help="Marine Animal Tracker port")
    args = parser.parse_args()

    if args.host is None:
        print("Please specify the IP Address of the Marine Animal Tracker")
        exit(1)
    if args.port is None:
        print("Please specify the Marine Animal Tracker port")
        exit(1)

    main(args.host, args.port)
