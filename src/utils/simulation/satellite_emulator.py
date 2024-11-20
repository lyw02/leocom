import os
import json
import hashlib
import time
import math
import random
import socket
import threading
import ast
import signal
import sys

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

from utils.encryption import SECRET_KEY
from ip_config import ground_station_host, ground_station_port


class SatelliteEmulator:

    def __init__(self, device_name, host, port, ground_ip, ground_port):
        self.device_name = device_name
        self.host = host
        self.port = int(port)
        self.ground_station_ip = ground_ip
        self.ground_station_port = int(ground_port)
        # self.gs = gs

        self.ground_lat = 53.3437967
        self.ground_long = -6.2571465

        self.delay_message = 0.0
        # self.latitude = random.uniform(-90.0, 90.0)
        # self.longitude = random.uniform(-180.0, 180.0)
        # self.altitude = 700.0  # in KMs
        # self.angle_increment = 0.1  # Controls speed of orbit simulation
        # self.current_angle = 0  # Starting angle
        
        self.orbit = {
            "init_lat": random.uniform(-90.0, 90.0),
            "init_long": random.uniform(-180.0, 180.0),
            "inclination": random.uniform(0.0, 180.0),
            "direction": random.choice([-1, 1]),
            "period": 3600 * random.uniform(0.0, 24.0) / 100, # make it move faster
            "start_time": time.time(),
            "altitude": 700.0
        }

        self.running = True

    def calculate_checksum(self, data):

        json_data = json.dumps(data, sort_keys=True).encode("utf-8")
        return hashlib.sha256(json_data).hexdigest()

    def decrypt_data(self, iv, encrypted_data, tag, key):
        cipher = Cipher(
            algorithms.AES(key), modes.GCM(iv, tag), backend=default_backend()
        )
        decryptor = cipher.decryptor()
        decrypted_data = decryptor.update(encrypted_data) + decryptor.finalize()

        return json.loads(decrypted_data.decode("utf-8"))

    def encrypt_data(self, data, key):
        iv = os.urandom(12)
        encryptor = Cipher(
            algorithms.AES(key), modes.GCM(iv), backend=default_backend()
        ).encryptor()

        data_bytes = json.dumps(data).encode("utf-8")

        ciphertext = encryptor.update(data_bytes) + encryptor.finalize()
        return iv, encryptor.tag, ciphertext
    
    def calculate_position(self, orbit):
        current_time = time.time()
        earth_rotation_rate = 360 / 86400
        
        t = current_time - orbit["start_time"]
        theta = (2 * math.pi * t) / orbit["period"]

        earth_rotation = earth_rotation_rate * t
        long = orbit["init_long"] + (theta * 180 / math.pi) * orbit["direction"] + earth_rotation
        long = (long + 180) % 360 - 180 

        lat = orbit["init_lat"] + math.sin(theta) * orbit["inclination"]
        lat = max(min(lat, 90), -90) 

        return lat, long

    def haversine(self, lat1, lon1, lat2, lon2):
        R = 6371.0
        
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c

    def handover_data(self, data):
        satellite_positions = ast.literal_eval(self.get_satellites_list())
        #satellite_positions = [sp for sp in satellite_positions if sp["addr"] != f"{self.host}:{self.port}"]
        satellite_positions = [sp for sp in satellite_positions if sp["device_name"] not in data["path"].split("-->")]
        satellite_positions.append({
            "device_name": 'GroundStation',
            "addr": f"{self.ground_station_ip}:{self.ground_station_port}",
            "orbit": {
                "init_lat": self.ground_lat,
                "init_long": self.ground_long
            }
        })
        min_distance = float('inf')
        closest_position = None
        print("\n")
        for position in satellite_positions:
            # position = json.loads(position)
            distance = 0
            #get latest geoposition of the satellite 
            self_lat, self_long = self.calculate_position(self.orbit)
            if position["device_name"] == "GroundStation":
                horizontal_distance = self.haversine(self_lat, self_long, self.ground_lat, self.ground_long)
                distance = horizontal_distance
                print(f"Distance to Ground Station : {distance}")
            else:
                lat, long = self.calculate_position(position["orbit"])
                horizontal_distance = self.haversine(self_lat, self_long, lat, long)
                # vertical_distance = abs(self.altitude - altitude)
                # distance = math.sqrt(horizontal_distance**2 + vertical_distance**2)
                distance = horizontal_distance
                print(f"Distance to ({lat},{long}) : {distance}")

            
            if distance < min_distance:
                min_distance = distance
                closest_position = position
    
        print(f"\nClosest Device: {closest_position['device_name']}")
        print(f"Shortest distance: {min_distance:.2f} km")

        #simulate delay based on distance
        speed_of_light = 299_792.458
        travel_time = min_distance / speed_of_light
        self.delay_message = travel_time
        
        if closest_position["device_name"] != 'GroundStation':
            
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as st:
                h, p = closest_position["addr"].split(":")
                #connect to closest satellite
                st.connect((h, int(p)))
                print(f"[{self.device_name}] Connected to {closest_position['device_name']} at {closest_position['addr']}")

                print(f"\nSimulating Message Travel Delay for {self.delay_message:.6f} seconds")
                time.sleep(self.delay_message)
                
                st.sendall(json.dumps(data).encode('utf-8'))
                print(f"[{self.device_name}] Data forwarded to Satellite {closest_position['device_name']} at {closest_position['addr']}")
                ack = st.recv(1024).decode('utf-8')
                if ack:
                    print(f"\n[{self.device_name}] Received acknowledgment from Satellite: {ack}")
        elif closest_position["device_name"] == 'GroundStation':
            self.forward_to_ground_station(data)
            
    # def handover_data_with_model_prediction(self, data):
    #     # load model
    #     model = tflite.Interpreter(model_path="model.tflite")
    #     model.allocate_tensors()
        
    #     # predict closest satellite
    #     ...

    def forward_to_ground_station(self, data):
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as gs:
            gs.connect((ground_station_host, int(ground_station_port)))

            print(f"\nSimulating Message Travel Delay for {self.delay_message:.6f} seconds")
            time.sleep(self.delay_message)
            
            gs.sendall(json.dumps(data).encode("utf-8"))
            print(f"[{self.device_name}] Data forwarded to  ground station.")
            ack = gs.recv(1024).decode("utf-8")
            if ack:
                print(f"\n[{self.device_name}] Received acknowledgment from Ground Station: {ack}")

    def register_to_network(self, network_host, network_port):
        #register satellite to the network
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((network_host, int(network_port)))
            self.server_socket = sock
            data = {
                "content": 'register ' + json.dumps({
                    "device_name": self.device_name, 
                    "addr": f"{self.host}:{self.port}",
                    "orbit": self.orbit
                })
            }
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
                self.network_host = network_host
                self.network_port = network_port

    def deregister_from_network(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((self.network_host, int(self.network_port)))
            data = {"content": f"deregister {self.host}:{self.port}"}
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
                    f"[{self.device_name}] {self.device_name} {self.host}:{self.port} Deregistered from network at {self.network_host}:{self.network_port}"
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
            res = res.decode('utf-8')
            print(f"\n[{self.device_name}] Received list of satellites:\n{res}")
            return res

    # Listen for data from trackers
    def listen_for_data(self):

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((self.host, self.port))
            s.listen()
            print(f"[{self.device_name}] Listening on {self.host}:{self.port}")

            try: 

                while self.running:

                    conn, addr = s.accept()
                    threading.Thread(
                        target=self.handle_tracker, args=(conn, addr), daemon=True
                    ).start()

            except KeyboardInterrupt:
                self.deregister_from_network()
                print("[Satellite] Shutting down gracefully")

    def handle_tracker(self, conn, addr):

        with conn:
            print(f"[{self.device_name}] Connection established with {addr}")
            while True:
                data = conn.recv(2048)
                if not data:
                    print(f"[{self.device_name}] Connection closed by {addr}")
                    break

                message = json.loads(data.decode("utf-8"))
                print(f"\n\n[{self.device_name}] Received data")
                message["path"] += "-->" + self.device_name

                print("\nMessage Travel Path: ", message["path"])

                try:
                    self.handover_data(message)
                except Exception as e:
                    print(f"Using ML model...")
                    
                ack_message = f"Data received and forwarded at {time.time()}"
                conn.sendall(ack_message.encode('utf-8'))
                print(f"\n[{self.device_name}] Forwarded Message and Sent acknowledgment back")
                
    

    def handle_sigterm(self, signal_number, frame):
        print("[Satellite] Shutting down gracefully")
        self.deregister_from_network()
        sys.exit(0)

    signal.signal(signal.SIGTERM, handle_sigterm)
