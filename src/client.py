import socket

from utils.message import parse_bob2_message
from utils.encryption import SECRET_KEY, decrypt_data
from utils.tags import DIVIDER, RESTORE


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
            buffer = b""

            encrypted_data = client_socket.recv(1024)

            if not encrypted_data:
                break
            buffer += encrypted_data

            while DIVIDER in buffer:
                message, buffer = buffer.split(DIVIDER, 1)
                if message:

                    if len(message) < 270: # TODO: detect anomaly message length
                        print("Unsafe massage length, ignore")
                        continue

                    restore = False
                    if message.startswith(RESTORE):
                        restore = True
                        message = message[3:]
                    else:
                        restore = False

                    # Decrypt the received data
                    decrypted_data = decrypt_data(message, SECRET_KEY).decode('utf-8')
                    
                    # Parse the decrypted message
                    msg_type, payload = parse_bob2_message(decrypted_data)
                    
                    if msg_type == "HELO":
                        print("Server says:\n", payload)
                    elif msg_type == "DATA" and restore:
                        print("Received Data (restored from message queue):\n", payload)
                    elif msg_type == "DATA" and not restore:
                        print("Received Data:\n", payload)
    except KeyboardInterrupt:
        print("Client stopping.")
    finally:
        client_socket.close()

client()
