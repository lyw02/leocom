import os
import socket
import hashlib
import json
import ast

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

from encryption import SECRET_KEY
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
        
            
def get_satellites_list():

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((registration_server_host, int(registration_server_port)))
        data = {"content": "get_list"}
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
        res = sock.recv(4096 * 4)
        res = res.decode('utf-8')
        print(f"Received list of satellites ({len(ast.literal_eval(res))}):\n{res}")
        return res


if __name__ == "__main__":
    get_satellites_list()
