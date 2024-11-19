import os
import socket
import hashlib
import json

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

from utils.encryption import SECRET_KEY
from ip_config import registration_server_host, registration_server_port


def calculate_checksum(data):
    json_data = json.dumps(data, sort_keys=True).encode('utf-8')
    return hashlib.sha256(json_data).hexdigest()


def encrypt_data(data, key):
        iv = os.urandom(12)  # Generate a random 12-byte IV
        encryptor = Cipher(
            algorithms.AES(key), modes.GCM(iv), backend=default_backend()
        ).encryptor()

        data_bytes = json.dumps(data).encode("utf-8")

        ciphertext = encryptor.update(data_bytes) + encryptor.finalize()
        return iv, encryptor.tag, ciphertext
        
            
def deregister(host, port):

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((registration_server_host, int(registration_server_port)))
        data = {"content": f"deregister {host}:{port}"}
        checksum = calculate_checksum(data)
        data["checksum"] = checksum
        iv, tag, encrypted_data = encrypt_data(
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
            print(f"Received acknowledgment: {ack}")
            print(
                f"Satellite at {host}:{port} deregistered from network"
            )


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Emulate a satellite")
    parser.add_argument('--host', type=str, help="Satellite IP address")
    parser.add_argument('--port', type=str, help="Satellite port")
    args = parser.parse_args()

    if args.host is None:
        print("Please specify the IP Address of the satellite")
        exit(1)
    if args.port is None:
        print("Please specify the satellite port")
        exit(1)
        
    deregister(args.host, args.port)
