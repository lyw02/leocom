import socket
import time
import threading
from queue import Queue

from utils.message import create_bob2_message
from utils.encryption import SECRET_KEY, encrypt_data
from utils.simulation import simulate_location_and_health
from utils.tags import DIVIDER, RESTORE


# Messages for each client
message_queues = {}
# Track which clients have started data generation
data_generation_started = set()

# Keep generating data and store into message queue
def generate_data(client_id):
    # If message queue of current client does not exisit then create a new queue
    if client_id not in message_queues:
        message_queues[client_id] = Queue()
        time.sleep(0.5)

    while True:
        data = simulate_location_and_health(socket.gethostname())
        bob2_message = create_bob2_message("DATA", data)

        # Store new message into message queue
        message_queues[client_id].put(bob2_message)

        time.sleep(2)

# Get message from message queue and send to client
def send_data(client_socket, client_id, addr):
    # Send initial "HELLO" message using BOB2 protocol with encryption
    hello_message = create_bob2_message("HELO", "Welcome to BOB2 Protocol Server")
    encrypted_hello = encrypt_data(hello_message, SECRET_KEY)
    client_socket.send(encrypted_hello + DIVIDER)

    # The queue of current client, if not exisit then create a new queue
    queue = message_queues.get(client_id, Queue())

    try:
        # If there are messages in queue, send them first
        stored_message = 0
        if not queue.empty():
            print(f"Connection with {addr} restored. Start sending queued messages.")
            stored_message = queue.qsize()
        
        # Send messages
        while True:
            if not queue.empty():
                bob2_message = queue.get()
                encrypted_message = encrypt_data(bob2_message, SECRET_KEY)
                if stored_message > 0:
                    client_socket.send(RESTORE + encrypted_message + DIVIDER)
                else:
                    client_socket.send(encrypted_message + DIVIDER)
                print(f"Sent data to {addr}.")

                queue.task_done()
                stored_message -= 1
                if stored_message > 0:
                    time.sleep(0.1)
            else:
                time.sleep(1)  # if queue is empty, check it later
    except (ConnectionAbortedError, ConnectionResetError):
        print(f"Client {addr} disconnected. Data will continue to be generated and wait for re-connection.")
    except KeyboardInterrupt:
        print("Server stopping.")
    finally:
        client_socket.close()
        print(f"Connection with {addr} closed.")

def handle_client(client_socket, addr):
    client_id = f"{addr[0]}:{addr[1]}"
    print(f"Client id: {client_id}")

    # Start the data generation thread only if it hasn't started for this client
    if client_id not in data_generation_started:
        threading.Thread(target=generate_data, args=(client_id,), daemon=True).start()
        data_generation_started.add(client_id)

    send_data(client_socket, client_id, addr)


def server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host = socket.gethostname()
    port = 12345
    
    server_socket.bind((host, port))
    print(f"Bind to port {port}.")
    server_socket.listen(5)
    print("Server listening for connections...")

    try:
        while True:
            client_socket, addr = server_socket.accept()  
            print(f"Connected to {addr}.")

            threading.Thread(target=handle_client, args=(client_socket, addr), daemon=True).start()
    except KeyboardInterrupt:
        print("Server stopping.")
    except ConnectionAbortedError:
        print("Client stopping, connection aborted.")
    finally:
        client_socket.close()
        server_socket.close()
        print("Server closed.")

server()
