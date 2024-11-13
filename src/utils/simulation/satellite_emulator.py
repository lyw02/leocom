import json
import hashlib
import time
import socket
import threading
import random
import math
import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from utils.encryption import SECRET_KEY

class SatelliteEmulator:
    def __init__(self, config):
        # Load satellite configuration
        self.host = config["host"]
        self.port = config["port"]
        self.latitude = config["latitude"]
        self.longitude = config["longitude"]
        self.altitude = config["altitude"]
        self.running = True
        self.data_store = {}  # Store data temporarily for disconnection handling

        # Start a thread to update the satellite's position continuously
        threading.Thread(target=self.update_position_loop, daemon=True).start()

    def update_position(self):
        # Simulate satellite movement by slightly adjusting latitude and longitude
        self.latitude += random.uniform(-0.05, 0.05)  # Adjust speed as needed
        self.longitude += random.uniform(-0.05, 0.05)

    def update_position_loop(self):
        """Continuously updates satellite position every few seconds to simulate movement."""
        while self.running:
            self.update_position()
            time.sleep(5)  # Adjust the interval for position updates

    def calculate_distance(self, lat1, lon1, alt1):
        """Calculate the 3D distance between satellite and a point (tracker or target)."""
        earth_radius = 6371  # Earth's radius in km
        lat2, lon2, alt2 = math.radians(self.latitude), math.radians(self.longitude), self.altitude

        # Convert to Cartesian coordinates
        x1 = (earth_radius + alt1) * math.cos(math.radians(lat1)) * math.cos(math.radians(lon1))
        y1 = (earth_radius + alt1) * math.cos(math.radians(lat1)) * math.sin(math.radians(lon1))
        z1 = (earth_radius + alt1) * math.sin(math.radians(lat1))

        x2 = (earth_radius + alt2) * math.cos(lat2) * math.cos(lon2)
        y2 = (earth_radius + alt2) * math.cos(lat2) * math.sin(lon2)
        z2 = (earth_radius + alt2) * math.sin(lat2)

        return math.sqrt((x2 - x1)**2 + (y2 - y1)**2 + (z2 - z1)**2)

    def find_closest_satellite(self, satellites, lat, lon, alt=0):
        """Finds the closest satellite to a given latitude, longitude, and altitude."""
        closest_satellite = None
        min_distance = float("inf")
        
        for satellite_name, satellite_data in satellites.items():
            distance = self.calculate_distance(satellite_data["latitude"], satellite_data["longitude"], satellite_data["altitude"])
            if distance < min_distance:
                min_distance = distance
                closest_satellite = satellite_name

        print(f"Closest satellite to ({lat}, {lon}, {alt} km) is {closest_satellite} with distance {min_distance:.2f} km")
        return closest_satellite

    def calculate_checksum(self, data):
        json_data = json.dumps(data, sort_keys=True).encode("utf-8")
        return hashlib.sha256(json_data).hexdigest()

    def decrypt_data(self, iv, encrypted_data, tag, key):
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=default_backend())
        decryptor = cipher.decryptor()
        decrypted_data = decryptor.update(encrypted_data) + decryptor.finalize()
        return json.loads(decrypted_data.decode("utf-8"))

    def listen_for_data(self):
        # Start listening for incoming tracker data
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((self.host, self.port))
            s.listen()
            print(f"[Satellite] Listening on {self.host}:{self.port}")

            while self.running:
                try:
                    conn, addr = s.accept()
                    threading.Thread(target=self.handle_tracker, args=(conn, addr), daemon=True).start()
                except KeyboardInterrupt:
                    print("[Satellite] Shutting down gracefully")

    def handle_tracker(self, conn, addr):
        with conn:
            print(f"[Satellite] Connection established with {addr}")
            while True:
                data = conn.recv(2048)
                if not data:
                    print(f"[Satellite] Connection closed by {addr}")
                    break

                message = json.loads(data.decode("utf-8"))
                iv = bytes.fromhex(message["iv"])
                encrypted_data = bytes.fromhex(message["encrypted_data"])
                tag = bytes.fromhex(message["tag"])

                try:
                    received_data = self.decrypt_data(iv, encrypted_data, tag, SECRET_KEY)
                    received_checksum = received_data.pop("checksum", None)
                    calculated_checksum = self.calculate_checksum(received_data)

                    if received_checksum == calculated_checksum:
                        print(f"[Satellite] Valid checksum from {received_data['device_name']}")
                        ack_message = f"Data received from {received_data['device_name']} at {time.time()}"
                        self.data_store[received_data["device_name"]] = received_data
                        self.route_data_to_target(received_data)
                    else:
                        print(f"[Satellite] Checksum mismatch!")
                        ack_message = "Error: Checksum mismatch detected!"

                    conn.sendall(ack_message.encode("utf-8"))
                    print(f"[Satellite] Acknowledgment sent to {received_data['device_name']}")

                except (ConnectionAbortedError, ConnectionResetError):
                    print(f"[Satellite] Connection aborted by {addr}.")
                except Exception as e:
                    print(f"[Satellite] Error in decryption: {e}")
                    conn.sendall(b"Error: Decryption failed")

    def route_data_to_target(self, data):
        """Finds the shortest path to the target satellite and sends the data."""
        target_lat, target_lon, target_alt = data["target_latitude"], data["target_longitude"], 0
        distance_to_target = self.calculate_distance(target_lat, target_lon, target_alt)
        print(f"[Satellite] Routing data to target satellite with distance: {distance_to_target} km")
        print(f"[Satellite] Data routed to target at ({target_lat}, {target_lon}, {target_alt} km)")

    def shutdown(self):
        self.running = False
        print("[Satellite] Shutdown complete.")

def load_config(satellite_name):
    # Load satellite configuration from JSON file
    with open("satellites_config.json", "r") as file:
        config = json.load(file)
    return config[satellite_name]

if __name__ == "__main__":
    # Identify satellite name using an environment variable or default to "Satellite-1"
    satellite_name = os.getenv("SATELLITE_NAME", "Satellite-1")
    config = load_config(satellite_name)
    satellite = SatelliteEmulator(config)
    satellite.listen_for_data()
