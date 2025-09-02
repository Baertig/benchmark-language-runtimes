# application name
APPLICATION = javascript_benchmark

# default BOARD environment
BOARD ?= native

# This has to be the absolute path to the RIOT base directory:
RIOTBASE ?= $(CURDIR)/../RIOT

# Comment this out to disable code in RIOT that does safety checking
# which is not needed in a production environment but helps in the
# development process:
DEVELHELP ?= 1

ifeq (,$(filter native native32 native64,$(BOARD)))
# Set stack size to something (conservatively) enormous
CFLAGS += -DTHREAD_STACKSIZE_MAIN=9092
endif

export JERRY_HEAP = 100 # KiB
export JERRY_STACK = 50 # KiB

# Add the package for Jerryscript
USEPKG += jerryscript

# Include ztimer for time measurements
USEMODULE += ztimer_usec
# generate .js.h header files of .js files
BENCHMARK ?= tarfind
BENCHMARK_FILE = $(BENCHMARK).js

BLOBS += benchmark.js

all: benchmark.js

.PHONY: .FORCE

benchmark.js: .FORCE
	cp $(BENCHMARK_FILE) benchmark.js

include $(RIOTBASE)/Makefile.include

include ../Makefile.include
