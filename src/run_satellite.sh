#!/bin/bash

pip install cryptography

port=$(shuf -i 33500-33600 -n 1)

name="Satellite_pi$(hostname -I | cut -d. -f4 | tr -d ' ')_$port"

nohup python3 satellite.py --name $name --host $(hostname -I) --port $port > satellite_$name_$(date +%Y-%m-%d_%H-%M-%S).log  2>&1 &

exit 0
