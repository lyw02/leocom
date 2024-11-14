import json
import hashlib
import time
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

    def forward_to_ground_station(self, gs, data):
        """with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as gs:
        gs.connect((self.ground_station_ip, self.ground_station_port))
        print(f"[Satellite] Connected to Ground Station at {self.ground_station_ip}:{self.ground_station_port}")
        """
        gs.sendall(json.dumps(data).encode("utf-8"))
        print("[Satellite] Data forwarded to ground station.")
        ack = gs.recv(1024).decode("utf-8")
        if ack:
            print(f"\n[Satellite] Received acknowledgment from Ground Station: {ack}")

    def register_to_network(self, network_host, network_port):
        """Register this satellite to the SatelliteNetwork."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((network_host, int(network_port)))
            sock.sendall(
                f"register {json.dumps({"device_name": self.device_name, "addr": f"{self.host}:{self.port}"})}".encode(
                    "utf-8"
                )
            )
            ack = sock.recv(1024).decode("utf-8")
            if ack:
                print(
                    f"[Satellite] {self.device_name} {self.host}:{self.port} Registered to network at {network_host}:{network_port}"
                )
                print(f"\n[{self.device_name}] Received acknowledgment: {ack}")
                self.network_host = network_host
                self.network_port = network_port
                
    def deregister_from_network(self):
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((self.network_host, int(self.network_port)))
            message = f"deregister {self.host} {self.port}"
            sock.sendall(message.encode('utf-8'))
            print(f"[Satellite] {self.device_name} {self.host}:{self.port} Deregistered from network at {self.network_host}:{self.network_port}")

    def get_satellites_list(self):
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((self.network_host, int(self.network_port)))
            sock.sendall(b"get_list")
            data = sock.recv(4096)
            print(f"[Satellite] Received list of satellites:\n{data.decode('utf-8')}")

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
