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
export JERRY_PROFILE ?= es5.1  # need for the Math module

# Add the package for Jerryscript
USEPKG += jerryscript

# Include ztimer for time measurements
USEMODULE += ztimer_usec
USEMODULE += libc_gettimeofday
# generate .js.h header files of .js files
BENCHMARK ?= tarfind
BENCHMARK_FILE = benchmarks/$(BENCHMARK).js

SCALE_FACTOR ?= 1
ITERATIONS ?= 1

CFLAGS += -DBENCH_ITERATIONS=$(ITERATIONS)

BLOBS += benchmark.js

all: benchmark.js

.PHONY: .FORCE

benchmark.js: .FORCE
	cp $(BENCHMARK_FILE) benchmark.js
	sed -i "s/SCALE_FACTOR = .*/SCALE_FACTOR = $(SCALE_FACTOR);/" benchmark.js
	@grep "SCALE_FACTOR =" benchmark.js

callgrind: all-valgrind
	valgrind --tool=callgrind $(ELFFILE)

flamegraph: all
	/usr/lib/linux-tools-6.8.0-79/perf record -g -- $(ELFFILE)
	stackcollapse-perf.pl out.perf > out.folded
	flamegraph.pl out.folded > benchmark.svg
	google-chrome benchmark.svg

include $(RIOTBASE)/Makefile.include

include ../Makefile.include
