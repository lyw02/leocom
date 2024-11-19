from utils.simulation.ground_station import GroundStationReceiver
from ip_config import ground_station_host, ground_station_port

    
station = GroundStationReceiver(ground_station_host, ground_station_port)
station.listen_for_data()
