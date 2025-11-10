# application name
APPLICATION = jerryscript_benchmark

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

HEAP ?= 100 #KiB
STACK ?= 5 #KiB
PROFILE ?= es5.1 # need for the Math module
MEM_STATS ?= OFF
ERROR_MESSAGES ?= ON
DUMP_BYTECODE ?= OFF

export JERRY_HEAP = $(HEAP) 
export JERRY_STACK = $(STACK) 
export JERRY_PROFILE = $(PROFILE)
export JERRY_MEM_STATS = $(MEM_STATS)
export JERRY_ERROR_MESSAGES = $(ERROR_MESSAGES)
export JERRY_PARSER_DUMP_BYTE_CODE = $(DUMP_BYTECODE)

ifeq ($(MEM_STATS),ON)
DEVELHELP = 1
CFLAGS += -DMEM_STATS
endif

ifeq ($(DUMP_BYTECODE),ON)
CFLAGS += -DDUMP_BYTECODE
endif

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

all: check_config benchmark.js

.PHONY: .FORCE

benchmark.js: .FORCE
	cp $(BENCHMARK_FILE) benchmark.js
	sed -i "s/SCALE_FACTOR = .*/SCALE_FACTOR = $(SCALE_FACTOR);/" benchmark.js
	@grep "SCALE_FACTOR =" benchmark.js

# rebuild jerryscript if config does not match
check_config: .FORCE
	CONFIG_NAME=.jerry_config_$(BOARD); \
	if [ ! -f $$CONFIG_NAME ] || [ "$$(cat $$CONFIG_NAME)" != "$(HEAP);$(STACK);$(PROFILE);$(MEM_STATS);$(ERROR_MESSAGES);$(DUMP_BYTECODE)" ]; then \
		echo "$(HEAP);$(STACK);$(PROFILE);$(MEM_STATS);$(ERROR_MESSAGES);$(DUMP_BYTECODE)" > $$CONFIG_NAME; \
		$(MAKE) clean; \
	fi
	@echo "Using JerryScript config: $(HEAP)KiB heap, $(STACK)KiB stack, profile=$(PROFILE), mem_stats=$(MEM_STATS), error_messages=$(ERROR_MESSAGES), dump_bytecode=$(DUMP_BYTECODE)"

callgrind: all-valgrind
	valgrind --tool=callgrind $(ELFFILE)

flamegraph: all
	/usr/lib/linux-tools-6.8.0-79/perf record -g -- $(ELFFILE)
	stackcollapse-perf.pl out.perf > out.folded
	flamegraph.pl out.folded > benchmark.svg
	google-chrome benchmark.svg

include $(RIOTBASE)/Makefile.include

include ../Makefile.include
