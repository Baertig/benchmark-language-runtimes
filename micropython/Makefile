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

benchmark.py:
	cp $(BENCHMARK_FILE) benchmark.py

include $(RIOTBASE)/Makefile.include
