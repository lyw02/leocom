import os
import logging
import json
import socket
import threading
import hashlib
from datetime import datetime

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

from utils.encryption import SECRET_KEY


def write_log(message):
    #storing logs for the network
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, f"log_network_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt")

    logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(message)s')

    logging.info(message)
    
class SatelliteNetwork:

    def __init__(self, registration_host, registration_port):
        self.satellites = []  
        self.current_satellite_index = 0

        self.registration_host = registration_host
        self.registration_port = int(registration_port)
        self.registration_server_running = True
        
    def calculate_checksum(self, data):
        """Calculate SHA-256 checksum of the JSON-encoded data."""
        json_data = json.dumps(data, sort_keys=True).encode('utf-8')
        return hashlib.sha256(json_data).hexdigest()

    def decrypt_data(self, iv, encrypted_data, tag , key):
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=default_backend())
        decryptor = cipher.decryptor()
        decrypted_data = decryptor.update(encrypted_data) + decryptor.finalize()

        
        return json.loads(decrypted_data.decode('utf-8'))

    def registration_server(self):
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((self.registration_host, self.registration_port))
            server_socket.listen()
            print(f"[Network] Registration server listening on {self.registration_host}:{self.registration_port}")
            write_log(f"[Network] Registration server listening on {self.registration_host}:{self.registration_port}")

            while self.registration_server_running:
                conn, addr = server_socket.accept()
                threading.Thread(
                    target=self.handle_registration, args=(conn, addr), daemon=True
                ).start()
                # self.handle_registration(conn, addr)

    def handle_registration(self, conn, addr):
        
        #Handle incoming registration requests from satellites
        with conn:

            while True:
                data = conn.recv(2048).decode('utf-8')
                if not data:
                    break

                message = json.loads(data)
                iv = bytes.fromhex(message["iv"])
                encrypted_data = bytes.fromhex(message["encrypted_data"])
                tag = bytes.fromhex(message["tag"])
                
                try:
                    received_data = self.decrypt_data(iv, encrypted_data, tag, SECRET_KEY)
                    received_checksum = received_data.pop("checksum", None)
                    calculated_checksum = self.calculate_checksum(received_data)

                    # Validate checksum
                    if received_checksum != calculated_checksum:
                        raise Exception
                    
                    data_content = received_data["content"]

                    if data_content.startswith("register"):
                        satellite_info = json.loads(data_content.split("register ")[1])
                        if not any(s.get("addr") == satellite_info.get("addr") for s in self.satellites):
                            self.satellites.append(satellite_info)
                            ack_message = f'Satellite registered at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
                            conn.sendall(ack_message.encode("utf-8"))
                            print(f"[Network] Registered satellite: {satellite_info}")
                            write_log(f"[Network] Registered satellite: {satellite_info}")
                        else:
                            ack_message = f"Satellite already registered"
                            conn.sendall(ack_message.encode("utf-8"))
                            print(f"[Network] Already registered satellite: {satellite_info}")
                            write_log(f"[Network] Already registered satellite: {satellite_info}")
                    elif data_content.startswith("deregister"):
                        satellite_info = data_content.split("deregister ")[1]
                        if any(satellite['addr'] == satellite_info for satellite in self.satellites):
                            self.satellites = [satellite for satellite in self.satellites if satellite['addr'] != satellite_info]
                            ack_message = f'Satellite deregistered at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
                            conn.sendall(ack_message.encode("utf-8"))
                            print(f"[Network] Deregistered satellite: {satellite_info}")
                            write_log(f"[Network] Deregistered satellite: {satellite_info}")
                    elif data_content == "get_list":
                        list_of_satellites = "".join(self.satellites.__str__())
                        conn.sendall(list_of_satellites.encode('utf-8'))
                        print("[Network] Sent list of satellites")
                        write_log("[Network] Sent list of satellites")
                    else:
                        ack_message = f'Incorrect command'
                        conn.sendall(ack_message.encode("utf-8"))
                        print(f"[Network] Incorrect command")
                        write_log("[Network] Incorrect command")
                except Exception as e:
                    print(f"[Network] Error in decryption/validation: {e}")
                    write_log(f"[Network] Error in decryption/validation: {e}")
                    conn.sendall(b"Error: Decryption failed")

    # def perform_handover(self):
    #     # Handover to the next satellite in network
    #     self.current_satellite_index = (self.current_satellite_index + 1) % len(
    #         self.satellites
    #     )
    #     current_satellite = self.satellites[self.current_satellite_index]
    #     print(
    #         f"Handover to Satellite {current_satellite.host}:{current_satellite.port}"
    #     )

    # def start_data_routing(self):
    #     # Start data routing and handover simulation
    #     while True:
    #         current_satellite = self.satellites[self.current_satellite_index]
    #         print(
    #             f"Routing data through Satellite {current_satellite.host}:{current_satellite.port}"
    #         )

    #         # Simulate data reception and processing delay
    #         time.sleep(2)

    #         # Trigger handover at random intervals to simulate network conditions
    #         if random.random() < 0.2:  # 20% chance of handover
    #             self.perform_handover()
