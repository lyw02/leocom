import os
import random
import json
import hashlib
import time
import socket
import threading
import queue
from datetime import datetime

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

from demo_utils.encryption import SECRET_KEY


class WildLifeTracker:

    def __init__(
        self,
        device_name,
        satellite_host,
        satellite_port,
        heart_rate_range,
        body_temperature_range,
    ):
        self.device_name = device_name
        self.satellite_host = satellite_host
        self.satellite_port = int(satellite_port)
        self.latitude = random.uniform(-90.0, 90.0)
        self.longitude = random.uniform(-180.0, 180.0)

        self.heart_rate = random.uniform(*heart_rate_range)
        self.body_temperature = random.uniform(*body_temperature_range)

        self.message_queue = queue.Queue()

    def collect_data(self, source_ip, source_port):
        # Simulate changes
        self.latitude += random.uniform(-0.001, 0.001)
        self.longitude += random.uniform(-0.001, 0.001)

        self.heart_rate += random.uniform(-0.5, 0.5)
        self.body_temperature += random.uniform(-0.1, 0.1)

        self.latitude = max(-90.0, min(90.0, self.latitude))
        self.longitude = max(-180.0, min(180.0, self.longitude))
        self.heart_rate = max(20, min(40, self.heart_rate))
        self.body_temperature = max(36.0, min(39.0, self.body_temperature))

        timestamp = time.time()

        data = {
            "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "device_name": self.device_name,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "heart_rate": self.heart_rate,
            "body_temperature": self.body_temperature,
            "timestamp": timestamp,
            "source_ip": source_ip,
            "source_port": source_port,
            "destination_ip": self.satellite_host,
            "destination_port": self.satellite_port,
        }

        return data

    def calculate_checksum(self, data):
        """Calculate SHA-256 checksum of the JSON-encoded data."""
        json_data = json.dumps(data, sort_keys=True).encode("utf-8")
        return hashlib.sha256(json_data).hexdigest()

    def encrypt_data(self, data, key):
        iv = os.urandom(12)  # Generate a random 12-byte IV
        encryptor = Cipher(
            algorithms.AES(key), modes.GCM(iv), backend=default_backend()
        ).encryptor()

        data_bytes = json.dumps(data).encode("utf-8")

        ciphertext = encryptor.update(data_bytes) + encryptor.finalize()
        # print('result of encrypt_data :',iv + encryptor.tag + ciphertext)
        return iv, encryptor.tag, ciphertext

    def sender_thread(self, secret_key):

        while True:

            try:
                # Establish a persistent connection to the satellite
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((self.satellite_host, self.satellite_port))
                    self.source_ip, self.source_port = s.getsockname()
                    print(
                        f"[{self.device_name}] Connected to satellite at {self.satellite_host}:{self.satellite_port}"
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
                            # Process data
                            checksum = self.calculate_checksum(data)
                            data["checksum"] = checksum
                            iv, tag, encrypted_data = self.encrypt_data(
                                data, secret_key
                            )
                            message = {
                                "iv": iv.hex(),
                                "encrypted_data": encrypted_data.hex(),
                                "tag": tag.hex(),
                            }
                            # Send the message
                            final_message = json.dumps(message)
                            print(
                                f"\n[{self.device_name}] Data to be sent to satellite: {json.dumps(data, indent=4)}"
                            )
                            s.sendall(final_message.encode("utf-8"))
                            print(f"\n[{self.device_name}] Sent encrypted data")

                            # Wait for acknowledgment
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
        """Continuously collect and send data every 2 seconds, maintaining a persistent connection."""
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
                ):  # If haven't connected, continue waiting
                    continue
                self.collect_data(self.source_ip, self.source_port)
                print(
                    f"[{self.device_name}] Adding data to message queue, {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
                time.sleep(5)
        except KeyboardInterrupt:
            print(f"[{self.device_name}] Stopping transmission")
        except Exception as e:
            print(f"[{self.device_name}] Error in communication: {e}")
