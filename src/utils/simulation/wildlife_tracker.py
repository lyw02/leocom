import os
import random
import json
import hashlib
import time
import socket
import threading
import queue
import math
import ast
from datetime import datetime

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

from utils.encryption import SECRET_KEY
from ip_config import registration_server_host, registration_server_port


class WildLifeTracker:

    def __init__(
        self,
        device_name,
        source_ip,
        source_port,
        heart_rate_range,
        body_temperature_range,
    ):
        self.device_name = device_name
        
        self.latitude = random.uniform(-90.0, 90.0)
        self.longitude = random.uniform(-180.0, 180.0)

        self.heart_rate = random.uniform(*heart_rate_range)
        self.body_temperature = random.uniform(*body_temperature_range)

        self.message_queue = queue.Queue()
        
        self.source_ip = source_ip
        self.source_port = source_port
        self.message_order = 0
        self.delay_message = 0.0

        
        # Get satellite list
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((registration_server_host, int(registration_server_port)))
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
            #print(f"\n[{self.device_name}] Received list of satellites:\n{res}")
            self.satellite_list = ast.literal_eval(res)

    def collect_data(self):
        # Simulate changes
        self.latitude += random.uniform(-0.001, 0.001)
        self.longitude += random.uniform(-0.001, 0.001)

        self.heart_rate += random.uniform(-0.5, 0.5)
        self.body_temperature += random.uniform(-0.1, 0.1)

        self.latitude = max(-90.0, min(90.0, self.latitude))
        self.longitude = max(-180.0, min(180.0, self.longitude))
        self.heart_rate = max(20, min(40, self.heart_rate))
        self.body_temperature = max(36.0, min(39.0, self.body_temperature))
        self.message_order += 1

        timestamp = time.time()

        data = {
            "Message Order": self.message_order,
            "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "device_name": self.device_name,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "heart_rate": self.heart_rate,
            "body_temperature": self.body_temperature,
            "timestamp": timestamp,
            "source_ip": self.source_ip,
            "source_port": self.source_port,
            # "destination_ip": self.satellite_host,
            # "destination_port": self.satellite_port,
        }

        return data

    def calculate_checksum(self, data):
        
        json_data = json.dumps(data, sort_keys=True).encode("utf-8")
        return hashlib.sha256(json_data).hexdigest()

    def encrypt_data(self, data, key):
        iv = os.urandom(12)  
        encryptor = Cipher(
            algorithms.AES(key), modes.GCM(iv), backend=default_backend()
        ).encryptor()

        data_bytes = json.dumps(data).encode("utf-8")

        ciphertext = encryptor.update(data_bytes) + encryptor.finalize()
        # print('result of encrypt_data :',iv + encryptor.tag + ciphertext)
        return iv, encryptor.tag, ciphertext

    def get_satellite_list(self):
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((registration_server_host, int(registration_server_port)))
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
            self.satellite_list = ast.literal_eval(res)

    def calculate_position(self, orbit):
        current_time = time.time()
        earth_rotation_rate = 360 / 86400
        
        t = current_time - orbit["start_time"]
        theta = (2 * math.pi * t) / orbit["period"]

        
        earth_rotation = earth_rotation_rate * t
        long = orbit["init_long"] + (theta * 180 / math.pi) * orbit["direction"] + earth_rotation
        long = (long + 180) % 360 - 180  

        # Calculate latitude
        lat = orbit["init_lat"] + math.sin(theta) * orbit["inclination"]
        lat = max(min(lat, 90), -90)  

        return lat, long
    
    def closest_satellite(self):
        closest_satellite = None
        min_distance = float('inf')
        
        h = None
        if self.height is not None:
            h = self.height / 1000
        elif self.depth is not None:
            h = -self.depth / 1000
        else:
            h = 0

        self.get_satellite_list()
        print('\n')
        for satellite in self.satellite_list:
            satellite_lat, satellite_lon = self.calculate_position(satellite["orbit"])
            distance = self.haversine_3d(self.latitude, self.longitude, h, satellite_lat, satellite_lon, satellite["orbit"]["altitude"])
            print(f"Distance to satellite at ({satellite_lat}, {satellite_lon}): {distance:.2f} km")

            if distance < min_distance:
                min_distance = distance
                closest_satellite = satellite

        print(f"Closest satellite is at ({closest_satellite['device_name']}, {closest_satellite['addr']})")
        
        speed_of_light = 299_792.458
        travel_time = min_distance / speed_of_light
        self.delay_message = travel_time
        #print(f"Simulating Travel Delay for {self.delay_message:.6f} seconds")
        #time.sleep(self.delay_message)
        
        return closest_satellite
                
    # def haversine(lat1, lon1, lat2, lon2):
    #     R = 6371  # Earth radius in kilometers
    #     phi1 = math.radians(lat1)
    #     phi2 = math.radians(lat2)
    #     delta_phi = math.radians(lat2 - lat1)
    #     delta_lambda = math.radians(lon2 - lon1)

    #     a = math.sin(delta_phi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2)**2
    #     c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    #     distance = R * c  # in kilometers
    #     return distance
    
    def haversine_3d(self, lat1, lon1, h1, lat2, lon2, h2):
        R = 6371  
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        
        a = math.sin(delta_phi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        d2 = R * c 

        
        delta_h = h2 - h1
        distance = math.sqrt(d2**2 + delta_h**2)  
        
        return distance

    def sender_thread(self, secret_key):
        #print("sender")

        while True:

            try:
                
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    #Check if Marine Tracker is generating data, then relay to surface marine node due to radio waves being unable to work in water
                    #This is a future work, based on research, not actually implemented currently.
                    if self.device_name.startswith("MarineAnimalTrackerDevice"):
                        print(f"[{self.device_name}] Relaying message through the closest node on the surface to LEO Satellites")
                    #finding closest satellite
                    closest_satellite = self.closest_satellite()
                    satellite_host, satellite_port = closest_satellite["addr"].split(":")
                    s.connect((satellite_host, int(satellite_port)))
                    self.source_ip, self.source_port = s.getsockname()
                    print(
                        f"[{self.device_name}] Connected to satellite at {satellite_host}:{satellite_port}"
                    )
                    print(
                        f"[{self.device_name}] Tracker IP: {self.source_ip}, Tracker Port: {self.source_port}"
                    )

                    queued_count = self.message_queue.qsize()
                    if queued_count > 0:
                        print(
                            f"[{self.device_name}] {queued_count} data in message queue, will send them first"
                        )
                    while True:

                        try:
                            data = self.message_queue.get_nowait()
                            data["restored"] = queued_count > 0
                            #calculate checksum and encrypt
                            checksum = self.calculate_checksum(data)
                            data["checksum"] = checksum
                            iv, tag, encrypted_data = self.encrypt_data(
                                data, secret_key
                            )
                            path = self.device_name
                            message = {
                                "iv": iv.hex(),
                                "encrypted_data": encrypted_data.hex(),
                                "tag": tag.hex(),
                                "path": path,
                            }
                            
                            final_message = json.dumps(message)
                            print(
                                f"\n[{self.device_name}] Data to be sent to satellite: {json.dumps(data, indent=4)}"
                            )
                            print(f"\nSimulating Message Travel Delay for {self.delay_message:.6f} seconds")
                            time.sleep(self.delay_message)
                            s.sendall(final_message.encode("utf-8"))
                            print(f"\n[{self.device_name}] Sent encrypted data")

                            
                            ack = s.recv(1024).decode("utf-8")
                            if ack:
                                print(
                                    f"\n[{self.device_name}] Received acknowledgment: {ack}"
                                )

                            queued_count -= 1
                            time.sleep(1)
                        except queue.Empty:
                            time.sleep(1)
                            continue
            except socket.error as e:
                print(
                    f"[{self.device_name}] Connection error: {e}, retrying in 5 seconds..."
                )
                time.sleep(5)

    def run(self):
        
        print(f"[{self.device_name}] Starting data transmission to satellite")
        print("Press Ctrl+C to stop\n")

        try:
            threading.Thread(
                target=self.sender_thread, args=(SECRET_KEY,), daemon=True
            ).start()

            while True:
                time.sleep(1)
                if not (
                    self.source_ip and self.source_port
                ):  
                    continue
                
                self.collect_data()
                print(
                    f"[{self.device_name}] Adding data to message queue, {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
                time.sleep(5)
        except KeyboardInterrupt:
            print(f"[{self.device_name}] Stopping transmission")
        except Exception as e:
            print(f"[{self.device_name}] Error in communication: {e}")
