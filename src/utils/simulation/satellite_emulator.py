import os
import json
import hashlib
import time
import math
import random
import socket
import threading

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

from utils.encryption import SECRET_KEY


class SatelliteEmulator:

    def __init__(self, device_name, host, port, ground_ip, ground_port, gs):
        self.device_name = device_name
        self.host = host
        self.port = int(port)
        self.ground_station_ip = ground_ip
        self.ground_station_port = int(ground_port)
        self.gs = gs

        self.ground_lat = 53.3437967
        self.ground_long = -6.2571465
        self.latitude = random.uniform(-90.0, 90.0)
        self.longitude = random.uniform(-180.0, 180.0)
        self.altitude = 700.0  # in KMs
        self.angle_increment = 0.1  # Controls speed of orbit simulation
        self.current_angle = 0  # Starting angle

        self.running = True

    def calculate_checksum(self, data):
        """Calculate SHA-256 checksum of the JSON-encoded data."""
        json_data = json.dumps(data, sort_keys=True).encode("utf-8")
        return hashlib.sha256(json_data).hexdigest()

    def decrypt_data(self, iv, encrypted_data, tag, key):
        cipher = Cipher(
            algorithms.AES(key), modes.GCM(iv, tag), backend=default_backend()
        )
        decryptor = cipher.decryptor()
        decrypted_data = decryptor.update(encrypted_data) + decryptor.finalize()

        # Convert back to dictionary
        return json.loads(decrypted_data.decode("utf-8"))

    def encrypt_data(self, data, key):
        iv = os.urandom(12)  # Generate a random 12-byte IV
        encryptor = Cipher(
            algorithms.AES(key), modes.GCM(iv), backend=default_backend()
        ).encryptor()

        data_bytes = json.dumps(data).encode("utf-8")

        ciphertext = encryptor.update(data_bytes) + encryptor.finalize()
        return iv, encryptor.tag, ciphertext
    
    def update_position(self):

        while True:
        # Simulate changes
            self.current_angle += self.angle_increment
            if self.current_angle >= 360:
                self.current_angle -= 360
            self.latitude = (self.latitude + math.sin(math.radians(self.current_angle)) * 0.5) % 90
            self.longitude = (self.longitude + math.cos(math.radians(self.current_angle)) * 0.5) % 180

            time.sleep(5)

    def haversine(self, lat1, lon1, lat2, lon2):
        # Radius of Earth in kilometers
        R = 6371.0
        
        # Convert degrees to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        # Distance in kilometers
        return R * c

    def handover_data(self, data):
        satellite_positions = [
                ('Satellite1', 34.05, -118.25, 700.0),  # Position 1: Los Angeles area, 500 km altitude
                ('Satellite2', 40.71, -74.00, 700.0),   # Position 2: New York area, 400 km altitude
                ('Satellite3', -33.86, 151.20, 700.0),  # Position 3: Sydney area, 600 km altitude
                ('Satellite4', 51.51, -0.13, 700.0),    # Position 4: London area, 550 km altitude
                ('Satellite5', 35.68, 139.69, 700.0)    # Position 5: Tokyo area, 450 km altitude
            ]
        satellite_positions.append(('Ground Station', self.ground_lat, self.ground_long, 700.0))
        min_distance = float('inf')
        closest_position = None
        for position in satellite_positions:
            name, latitude, longitude, altitude = position
            #print('\nName : ', name)
            #print('latitude : ', latitude)
            #print('longitude : ', longitude)
            #print('altitude : ', altitude)
            horizontal_distance = self.haversine(self.latitude, self.longitude, latitude, longitude)
            vertical_distance = abs(self.altitude - altitude)
            distance = math.sqrt(horizontal_distance**2 + vertical_distance**2)
            #distance = calculate_3d_distance(my_lat, my_long, my_alt, latitude, longitude, altitude)
            #print('distance : ',distance)
            if distance < min_distance:
                min_distance = distance
                closest_position = position
    
        print(f"\nClosest satellite position: {closest_position[0]}")
        print(f"Shortest distance: {min_distance:.2f} km")
        
        if closest_position[0] != 'Ground Station':
            
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as st:
                st.connect(("127.0.0.1", 5005))
                print(f"[Satellite] Connected to {closest_position[0]} at 127.0.0.1:5005")

                st.sendall(json.dumps(data).encode('utf-8'))
                print("[Satellite] Data forwarded to Satellite.")
                ack = st.recv(1024).decode('utf-8')
                if ack:
                    print(f"\n[Satellite] Received acknowledgment from Ground Station: {ack}")
        elif closest_position[0] == 'Ground Station':
            self.forward_to_ground_station(self.gs, data)

    def forward_to_ground_station(self, gs, data):
        gs.sendall(json.dumps(data).encode("utf-8"))
        print("[Satellite] Data forwarded to ground station.")
        ack = gs.recv(1024).decode("utf-8")
        if ack:
            print(f"\n[Satellite] Received acknowledgment from Ground Station: {ack}")

    def register_to_network(self, network_host, network_port):
        """Register this satellite to the SatelliteNetwork."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((network_host, int(network_port)))
            data = {"content": f'register {json.dumps({"device_name": self.device_name, "addr": f"{self.host}:{self.port}"})}'}
            checksum = self.calculate_checksum(data)
            data["checksum"] = checksum
            iv, tag, encrypted_data = self.encrypt_data(
                data, SECRET_KEY
            )
            message = {
                "iv": iv.hex(),
                "encrypted_data": encrypted_data.hex(),
                "tag": tag.hex(),
            }
            final_message = json.dumps(message)
            sock.sendall(final_message.encode("utf-8"))
            print("sent")
            ack = sock.recv(1024).decode("utf-8")
            print(f"ack: {ack}")
            if ack:
                # print(
                #     f"[Satellite] {self.device_name} {self.host}:{self.port} Registered to network at {network_host}:{network_port}"
                # )
                print(f"\n[{self.device_name}] Received acknowledgment: {ack}")
                self.network_host = network_host
                self.network_port = network_port

    def deregister_from_network(self):

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((self.network_host, int(self.network_port)))
            data = {"content": f"deregister {self.host} {self.port}"}
            checksum = self.calculate_checksum(data)
            data["checksum"] = checksum
            iv, tag, encrypted_data = self.encrypt_data(
                data, SECRET_KEY
            )
            message = {
                "iv": iv.hex(),
                "encrypted_data": encrypted_data.hex(),
                "tag": tag.hex(),
            }
            final_message = json.dumps(message)
            sock.sendall(final_message.encode("utf-8"))
            ack = sock.recv(1024).decode("utf-8")
            if ack:
                print(f"\n[{self.device_name}] Received acknowledgment: {ack}")
                print(
                    f"[Satellite] {self.device_name} {self.host}:{self.port} Deregistered from network at {self.network_host}:{self.network_port}"
                )

    def get_satellites_list(self):

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((self.network_host, int(self.network_port)))
            data = {"content": "get_list"}
            checksum = self.calculate_checksum(data)
            data["checksum"] = checksum
            iv, tag, encrypted_data = self.encrypt_data(
                data, SECRET_KEY
            )
            message = {
                "iv": iv.hex(),
                "encrypted_data": encrypted_data.hex(),
                "tag": tag.hex(),
            }
            final_message = json.dumps(message)
            sock.sendall(final_message.encode("utf-8"))
            res = sock.recv(4096)
            print(f"[Satellite] Received list of satellites:\n{res.decode('utf-8')}")

    # Listen for data from trackers and send acknowledgment
    def listen_for_data(self):

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((self.host, self.port))
            s.listen()
            print(f"[Satellite] Listening on {self.host}:{self.port}")

            while self.running:

                try:
                    conn, addr = s.accept()
                    threading.Thread(
                        target=self.handle_tracker, args=(conn, addr)
                    ).start()

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
                print(f"\n\n[Satellite] Received data")

                self.forward_to_ground_station(self.gs, message)
                ack_message = (
                    f"Data received and forwarded to Ground Station at {time.time()}"
                )
                conn.sendall(ack_message.encode("utf-8"))
                print(
                    f"\n[Satellite] Forwarded Message to Ground Station and Sent acknowledgment back"
                )

    def shutdown(self):
        self.running = False
        self.deregister_from_network(self.network_host, self.network_port)
        self.server_socket.close()
        print("[Satellite] Shutdown")
