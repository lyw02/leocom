import socket

from utils.message import parse_bob2_message
from utils.encryption import SECRET_KEY, decrypt_data


def client():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host = socket.gethostname()

    client_port = 12346
    client_socket.bind((host, client_port))
    print(f"Bind to port {client_port}")
    
    server_port = 12345
    client_socket.connect((host, server_port))
    print("Connected to server.")

    try:
        while True:
            encrypted_data = client_socket.recv(1024)
            if encrypted_data:
                # Decrypt the received data
                decrypted_data = decrypt_data(encrypted_data, SECRET_KEY).decode('utf-8')
                
                # Parse the decrypted message
                msg_type, payload = parse_bob2_message(decrypted_data)
                
                if msg_type == "HELLO":
                    print("Server says:", payload)
                elif msg_type == "DATA":
                    print("Received Data:", payload)
    except KeyboardInterrupt:
        print("Client stopping.")
    finally:
        client_socket.close()

client()
