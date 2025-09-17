APPLICATION = micropython

BOARD ?= native

RIOTBASE ?= $(CURDIR)/../RIOT

USEPKG += micropython
USEMODULE += ztimer_usec

BENCHMARK ?= tarfind
BENCHMARK_FILE = $(BENCHMARK).py

BLOBS += benchmark.py

# configure MicroPython's heap size
MP_RIOT_HEAPSIZE ?= $(shell echo $$((32 * 1024)))

# MicroPython needs a larger stack
CFLAGS += '-DTHREAD_STACKSIZE_MAIN=THREAD_STACKSIZE_DEFAULT*4'

# use miniterm (instead of the default pyterm) in order to support control
# characters (CTRL-D ...)
# RIOT_TERMINAL ?= miniterm

all: benchmark.py

.PHONY: .FORCE

benchmark.py: .FORCE
	cp $(BENCHMARK_FILE) benchmark.py

flamegraph: all
	sudo /usr/lib/linux-tools-6.8.0-79/perf record -g -- $(ELFFILE)
	sudo chown georg-baer-dumont:georg-baer-dumont ./perf.data
	/usr/lib/linux-tools-6.8.0-79/perf script > out.perf
	stackcollapse-perf.pl out.perf > out.folded
	flamegraph.pl out.folded > benchmark.svg
	google-chrome benchmark.svg

include $(RIOTBASE)/Makefile.include

include ../Makefile.include
