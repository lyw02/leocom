import socket
import time

from utils.message import create_bob2_message
from utils.encryption import SECRET_KEY, encrypt_data
from utils.simulation import simulate_location_and_health


def server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host = socket.gethostname()
    port = 12345
    
    server_socket.bind((host, port))
    print(f"Bind to port {port}")
    server_socket.listen(5)
    print("Server listening for connections...")

    client_socket, addr = server_socket.accept()  
    print(f"Connected to {addr}")

    # Send initial "HELLO" message using BOB2 protocol with encryption
    hello_message = create_bob2_message("HELLO", "Welcome to BOB2 Protocol Server")
    encrypted_hello = encrypt_data(hello_message, SECRET_KEY)
    client_socket.send(encrypted_hello)

    try:
        while True:
            # Generate location and health message
            data = simulate_location_and_health(host)
            bob2_message = create_bob2_message("DATA", data)
            
            # Encrypt the BOB2 message before sending
            encrypted_message = encrypt_data(bob2_message, SECRET_KEY)
            client_socket.send(encrypted_message)
            time.sleep(2)
    except KeyboardInterrupt:
        print("Server stopping.")
    finally:
        client_socket.close()

server()
