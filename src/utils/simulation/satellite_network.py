import time
import json
import socket
import threading


class SatelliteNetwork:

    def __init__(self, registration_host, registration_port):
        self.satellites = []  # List of SatelliteEmulator instances
        self.current_satellite_index = 0

        self.registration_host = registration_host
        self.registration_port = int(registration_port)
        self.registration_server_running = True
        self.registration_server_thread = threading.Thread(
            target=self.registration_server
        )
        self.registration_server_thread.start()

    def registration_server(self):
        """Server that allows satellites to register themselves."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((self.registration_host, self.registration_port))
            server_socket.listen()
            print(
                f"[Network] Registration server listening on {self.registration_host}:{self.registration_port}"
            )

            while self.registration_server_running:
                conn, addr = server_socket.accept()
                threading.Thread(
                    target=self.handle_registration, args=(conn, addr)
                ).start()

    def handle_registration(self, conn, addr):
        """Handle incoming registration requests from satellites."""
        with conn:

            while True:
                data = conn.recv(1024).decode('utf-8')
                if not data:
                    break

                if data.startswith("register"):
                    satellite_info = json.loads(data.split("register ")[1])
                    self.satellites.append(satellite_info)
                    ack_message = f"Satellite registered at {time.time()}"
                    conn.sendall(ack_message.encode("utf-8"))
                    print(f"[Network] Registered satellite at {satellite_info}")
                elif data.startswith("deregister"):
                    satellite_info = data.split("deregister ")[1]
                    if satellite_info in self.satellites:
                        self.satellites.remove(satellite_info)
                        ack_message = f"Satellite deregistered at {time.time()}"
                        conn.sendall(ack_message.encode("utf-8"))
                        print(f"[Network] Deregistered satellite at {satellite_info}")
                elif data == "get_list":
                    list_of_satellites = "".join(self.satellites.__str__())
                    conn.sendall(list_of_satellites.encode('utf-8'))
                    print("[Network] Sent list of satellites")

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
