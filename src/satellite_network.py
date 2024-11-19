from utils.simulation.satellite_network import SatelliteNetwork
from ip_config import registration_server_host, registration_server_port


# Start registeration server
satellite_network = SatelliteNetwork(registration_server_host, registration_server_port)
satellite_network.registration_server()
