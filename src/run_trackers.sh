#!/bin/bash

n=5

start_port=33200

trackers=("bird_tracker.py" "marine_animal_tracker.py" "terrestrial_animal_tracker.py")

host=$(hostname -i)

for ((i=0; i<n; i++))
do
  port=$(($start_port + i))

  tracker=${trackers[$RANDOM % ${#trackers[@]}]}

  nohup python3 $tracker --host $host --port $port &

  echo "Running $tracker on $host:$port"
done
