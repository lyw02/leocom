### Low Earth Orbit Satellites Communication

Install:

```sh
pip -r requirements.txt
```

Start in two different terminals:

```sh
cd src

python3 satellite_network.py

python3 ground_station.py

python3 satellite.py --name "Satellite-01" --host "10.35.70.20" --port 33700

python3 bird_tracker.py

python3 marine_animal_tracker.py

python3 terrestrial_animal_tracker.py
```
