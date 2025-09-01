bench: 
	pipenv run ./benchmark.py --config benchmark-config.yml --board native --write-csv bench.csv

bench-feather:
	pipenv run ./benchmark.py --config benchmark-config.yml --board adafruit-feather-nrf52840-sense --write-csv bench-feather.csv --port /dev/ttyACM1

bench-esp32-wroom-32:
	pipenv run ./benchmark.py --config benchmark-config.yml --board esp32-wroom-32 --write-csv bench-esp32-wroom-32.csv --port /dev/ttyACM0


