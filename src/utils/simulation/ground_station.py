import socket
import json
import time
import hashlib
import threading
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from utils.encryption import SECRET_KEY

import logging
import os
import datetime

def write_log(message):

    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, f"log_ground_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt")

    logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(message)s')

    logging.info(message)

class GroundStationReceiver:
    def __init__(self, host, port):
        self.host = host
        self.port = int(port)

    def calculate_checksum(self, data):
        json_data = json.dumps(data, sort_keys=True).encode('utf-8')
        return hashlib.sha256(json_data).hexdigest()

    def decrypt_data(self, iv, encrypted_data, tag , key):
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=default_backend())
        decryptor = cipher.decryptor()
        decrypted_data = decryptor.update(encrypted_data) + decryptor.finalize()

        return json.loads(decrypted_data.decode('utf-8'))


    def listen_for_data(self):
        #Listen for data from Satellite and send acknowledgment.
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.host, self.port))
            s.listen()
            print(f"[Ground Station] Listening on {self.host}:{self.port}")

            try:
                while True:
                    conn, addr = s.accept()
                    threading.Thread(target=self.handle_tracker, args=(conn, addr)).start()                            

            except KeyboardInterrupt:
                print("[Ground Station] Shutting down gracefully")

    def handle_tracker(self, conn, addr):
        with conn:
            print(f"[Ground Station] Connection established with {addr}")
            while True:
                data = conn.recv(4096)
                if not data:
                    print(f"[Ground Station] Connection closed by {addr}")
                    break

                # received_data = json.loads(data.decode('utf-8'))

                message = json.loads(data.decode('utf-8'))
                iv = bytes.fromhex(message["iv"])
                encrypted_data = bytes.fromhex(message["encrypted_data"])
                tag = bytes.fromhex(message["tag"])
                path = message["path"] + "-->Ground Station\n"
                print("\nMessage Travel Path: ", path)
                write_log('\nMessage Travel Path: ' + str(path))
                '''received_data = json.loads(data.decode('utf-8'))

                ack_message = f"Data received from {received_data['device_name']} at {time.time()}"
                print(f"\n\n[Ground Station] Received data from {received_data['device_name']}: {received_data}")
                conn.sendall(ack_message.encode('utf-8'))
                print(f"\n[Ground Station] Sent acknowledgment to Satellite")'''

                try:
                    #decrypt received data
                    received_data = self.decrypt_data(iv, encrypted_data, tag, SECRET_KEY)
                    final_time = time.time()
                    initial_time = received_data['timestamp']
                    #calculate latency
                    print('\nTotal Time taken in message travel : ',final_time - initial_time)
                    write_log('Total Time taken in message travel : ' + str(final_time - initial_time))
                
                    #remove shared checksum and recalculate
                    received_checksum = received_data.pop("checksum", None)
                    calculated_checksum = self.calculate_checksum(received_data)

                    # Validating checksum
                    if received_checksum == calculated_checksum:
                        print(f"[Ground Station] Data received successfully with valid checksum: {received_checksum}")
                        ack_message = f"Data received from Satellite at {final_time}"
                        print(f"\n\n[Ground Station] Received data : {received_data}")
                        write_log('Received Data : ' + str(received_data) + '\n')
                    else:
                        print(f"[Ground Station] Checksum mismatch! Received: {received_checksum}, Calculated: {calculated_checksum}")
                        ack_message = "\nError: Checksum mismatch detected!"
                        write_log('Checksum mismatch! Received: ' + str(received_checksum) +', Calculated: ' + str(calculated_checksum) + '\n')
                    

                    # Send acknowledgment back to the tracker
                    conn.sendall(ack_message.encode('utf-8'))
                    print(f"\n[Ground Station] Sent acknowledgment to Satellite")

                except Exception as e:
                    print(f"[Ground Station] Error in decryption/validation: {e}")
                    conn.sendall(b"Error: Decryption failed")
