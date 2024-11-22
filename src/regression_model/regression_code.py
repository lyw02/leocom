import numpy as np
import joblib

# Load the saved model
model = joblib.load('satellite_position_predictor.pkl')

# Input parameters for prediction (example: current time, inclination, altitude, velocity)
time = 12.0  # Time in hours
inclination = 45.0  # Inclination in degrees
altitude = 1000.0  # Altitude in km
velocity = 7.5  # Velocity in km/s

# Create input array
input_data = np.array([[time, inclination, altitude, velocity]])

# Predict satellite position
predicted_position = model.predict(input_data)

# Display predicted position
x, y, z = predicted_position[0]
print(f"Predicted Satellite Position:\nX: {x:.2f} km\nY: {y:.2f} km\nZ: {z:.2f} km")
