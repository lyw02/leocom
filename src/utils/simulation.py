import random

def simulate_location_and_health(device_name):
    latitude = random.uniform(-90.0, 90.0)
    longitude = random.uniform(-180.0, 180.0)
    depth = random.uniform(0, 11000)
    heart_rate = random.uniform(20, 40)
    body_temperature = random.uniform(36.0, 39.0)
    
    msg = (f"Device: {device_name}\n"
           f"Latitude: {latitude:.6f}, Longitude: {longitude:.6f}, Depth: {depth:.2f} m\n"
           f"Heart Rate: {heart_rate:.1f} bpm, Body Temperature: {body_temperature:.1f} °C")
    return msg
