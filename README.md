### Wildlife Tracking System through LEO Satellites using LowConnect P2P Protocol

#### CS7NS1 Project 3 Group Code Repository

##### Group 16
- Yiwei Liu (24337730) 
- Akshay Arora (24338068) 
- Archana Ajikumar Nair (24367486) 
- Abhigyan Khaund (24367958) 

##### Instructions

You can start emulation on one Pi with one script: 

```sh
cd src

bash runme.sh
```

This command will run a registration server, a ground station, 5 satellites and 5 random trackers on current Pi.

Use command to see output:

```sh
vi ground_station.log
```

Or you can also run every component separately on different Pi's:

```sh
# In src directory
cd src

# Edit IP and port of registration server and ground station
vi ip_config

# Start the registration server
python3 satellite_network.py

# Start the ground station
python3 ground_station.py

# Start a satellite emulator
python3 satellite.py --name <satellite_name> --host <satellite_ip> --port <satellite_port>

# Start different types of trackers
python3 bird_tracker.py --host <tracker_ip> --port <tracker_port>
python3 marine_animal_tracker.py --host <tracker_ip> --port <tracker_port>
python3 terrestrial_animal_tracker.py --host <tracker_ip> --port <tracker_port>
```

We also implemented a ML model in `/src/regression_model`. However, it hasn't been integrated into our network, so it should be run separately, out of Pi:

Install : 

```sh
pip install numpy pandas scikit-learn joblib
```

Model: The trained model is saved as `satellite_position_predictor.pkl`

Script: 

```sh
cd regression_model

python3 regression_code.py
```

Output: Predicted satellite position in 3D space (X, Y, Z coordinates).
