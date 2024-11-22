#!/bin/bash

pip install cryptography

# Update ip_config.py
cat << EOF > ip_config.py
#!/usr/bin/env python3

pi_1_ip = "$(hostname -i)"
pi_2_ip = "$(hostname -i)"

registration_server_host = pi_1_ip
registration_server_port = 33500

ground_station_host = pi_2_ip
ground_station_port = 33600
EOF

echo "ip_config.py updated"

# Start registration server
nohup python3 -u satellite_network.py > registration_server.log  2>&1 &
echo "Running Registration Server on $(hostname -i):33500"

# Start ground station
nohup python3 -u ground_station.py > ground_station.log  2>&1 &
echo "Running Ground Station on $(hostname -i):33600"

# Start 5 satellites
for i in {1..5}
do
    port=$((33700 + i))
    name="Satellite_pi$(hostname -I | cut -d. -f4 | tr -d ' ')_$port"
    nohup python3 satellite.py --name $name --host $(hostname -I) --port $port > satellite_$name.log  2>&1 &
    echo "Running $name on $(hostname -i):$port"
done

# Start 5 radom trackers
trackers=("bird_tracker.py" "marine_animal_tracker.py" "terrestrial_animal_tracker.py")
for i in {1..5}
do
    random_tracker=$(printf "%s\n" "${trackers[@]}" | shuf -n 1)
    port=$((33800 + i))
    nohup python3 $random_tracker --host $(hostname -i) --port $port > tracker_$port.log  2>&1 &
    echo "Running $random_tracker on $(hostname -i):$port"
done
