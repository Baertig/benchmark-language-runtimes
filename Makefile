RUNTIME_DIR = data/runtime

bench:
	mkdir -p $(RUNTIME_DIR)
	pipenv run ./scripts/benchmark.py --config benchmark-config.yml --board native --write-csv $(RUNTIME_DIR)/bench.csv

bench-feather:
	mkdir -p $(RUNTIME_DIR)
	pipenv run ./scripts/benchmark.py --config benchmark-config.yml --board adafruit-feather-nrf52840-sense --write-csv $(RUNTIME_DIR)/bench-feather.csv --port /dev/ttyACM1

bench-esp32-wroom-32:
	mkdir -p $(RUNTIME_DIR)
	pipenv run ./scripts/benchmark.py --config benchmark-config.yml --board esp32-wroom-32 --write-csv $(RUNTIME_DIR)/bench-esp32-wroom-32.csv

measure-memory:
	mkdir -p data/memory figures/memory
	pipenv run ./scripts/measure_memory.py --config benchmark-config.yml --csv-out data/memory/memory-sizes.csv --figures figures/memory --mappings scripts/symbol-mappings.yml


