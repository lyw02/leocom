import json
import hashlib
import time
import socket
import threading

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

from demo_utils.encryption import SECRET_KEY


class SatelliteEmulator:

    def __init__(self, host, port):
        self.host = host
        self.port = int(port)

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

    # Listen for data from trackers and send acknowledgment
    def listen_for_data(self):

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((self.host, self.port))
            s.listen()
            print(f"[Satellite] Listening on {self.host}:{self.port}")

            while self.running:

                try:
                    conn, addr = s.accept()
                    threading.Thread(
                        target=self.handle_tracker, args=(conn, addr), daemon=True
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
                iv = bytes.fromhex(message["iv"])
                encrypted_data = bytes.fromhex(message["encrypted_data"])
                tag = bytes.fromhex(message["tag"])

                # Decrypt data
                try:
                    received_data = self.decrypt_data(
                        iv, encrypted_data, tag, SECRET_KEY
                    )

                    received_checksum = received_data.pop("checksum", None)
                    calculated_checksum = self.calculate_checksum(received_data)

                    # Validate checksum
                    if received_checksum == calculated_checksum:
                        print(
                            f"[Satellite] Data received successfully with valid checksum: {received_checksum}"
                        )
                        ack_message = f"Data received from {received_data['device_name']} at {time.time()}"
                        print(
                            f"\n\n[Satellite] Received data from {received_data['device_name']}: {json.dumps(received_data, indent=4)}"
                        )
                    else:
                        print(
                            f"[Satellite] Checksum mismatch! Received: {received_checksum}, Calculated: {calculated_checksum}"
                        )
                        ack_message = "Error: Checksum mismatch detected!"

                    # Send acknowledgment back to the tracker
                    # ack_message = f"Data received from {received_data['device_name']} at {received_data['timestamp']}"
                    # ack_message = f"Data received from {received_data['device_name']} at {time.time()}"
                    conn.sendall(ack_message.encode("utf-8"))
                    print(
                        f"\n[Satellite] Sent acknowledgment to {received_data['device_name']}"
                    )

                except (ConnectionAbortedError, ConnectionResetError):
                    print(f"[Satellite] Connection aborted by {addr}.")

                except Exception as e:
                    print(f"[Satellite] Error in decryption/validation: {e}")
                    conn.sendall(b"Error: Decryption failed")

    def shutdown(self):
        self.running = False
        self.server_socket.close()
        print("[Satellite] Shutdown")
