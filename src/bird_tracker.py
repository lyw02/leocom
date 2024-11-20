import random
from utils.simulation.wildlife_tracker import WildLifeTracker

#imports WildLifeTracker which controls all trackers
class BirdTracker(WildLifeTracker):

    def __init__(
        self,
        device_name,
        source_ip,
        source_port,
        heart_rate_range=(100, 600),
        body_temperature_range=(39.0, 43.0),
    ):
        super().__init__(
            device_name,
            source_ip,
            source_port,
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

def main(host, port):
    name = "BirdTrackerDevice" + str(random.randint(1, 1000))
    tracker = BirdTracker(name, host, port)
    tracker.run()

if __name__ == "__main__":
    import argparse
    #takes IP Address and port of this tracker as argument
    parser = argparse.ArgumentParser(description="Emulate a bird tracker")
    parser.add_argument('--host', type=str, help="Bird Tracker IP address")
    parser.add_argument('--port', type=str, help="Bird Tracker port")
    args = parser.parse_args()

    if args.host is None:
        print("Please specify the IP Address of the Bird Tracker")
        exit(1)
    if args.port is None:
        print("Please specify the Bird Tracker port")
        exit(1)

    main(args.host, args.port)
