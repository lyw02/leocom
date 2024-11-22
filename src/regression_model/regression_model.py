import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error
import joblib

# Generate synthetic data for satellite orbits (or load real data if available)
# Features: time, inclination, altitude, velocity
# Target: x, y, z position in 3D space
np.random.seed(42)
data_size = 1000
time = np.linspace(0, 24, data_size)  # time in hours
inclination = np.random.uniform(0, 180, data_size)  # inclination in degrees
altitude = np.random.uniform(500, 2000, data_size)  # altitude in km
velocity = np.random.uniform(7, 8, data_size)  # velocity in km/s
x = altitude * np.cos(np.radians(inclination)) * np.cos(2 * np.pi * time / 24)
y = altitude * np.sin(np.radians(inclination)) * np.cos(2 * np.pi * time / 24)
z = altitude * np.sin(2 * np.pi * time / 24)

# Create a DataFrame
df = pd.DataFrame({
    'time': time,
    'inclination': inclination,
    'altitude': altitude,
    'velocity': velocity,
    'x': x,
    'y': y,
    'z': z
})

# Split data into training and testing sets
X = df[['time', 'inclination', 'altitude', 'velocity']]
y = df[['x', 'y', 'z']]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train a Random Forest Regressor
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Evaluate the model
y_pred = model.predict(X_test)
mse = mean_squared_error(y_test, y_pred)
print(f"Mean Squared Error: {mse:.2f}")

# Save the trained model
joblib.dump(model, 'satellite_position_predictor.pkl')
print("Model saved as 'satellite_position_predictor.pkl'")
