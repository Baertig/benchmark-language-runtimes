# name of your application
APPLICATION = wamr_benchmark

# Change this to your board if you want to build for a different board
BOARD ?= native

# This has to be the absolute path to the RIOT base directory:
RIOTBASE ?= $(CURDIR)/../RIOT

USEPKG += wamr
USEMODULE += ztimer_usec

# Select which benchmark to compile
BENCHMARK ?= tarfind
BENCHMARK_FILE = $(BENCHMARK).c


ifeq (,$(filter native native32 native64,$(BOARD)))
CFLAGS += -DTHREAD_STACKSIZE_MAIN='(6 * 1024)'
endif

BLOBS += benchmark.wasm

# to enable: "DWASM_ENABLE_OPCODE_COUNTER=1"
# go there RIOT/build/pkg/wamr/core/config.h:295

# Comment this out to disable code in RIOT that does safety checking
# which is not needed in a production environment but helps in the
# development process:
DEVELHELP ?= 1
SCALE_FACTOR ?= 1
ITERATIONS ?= 1
HEAP ?= 16384
STACK ?= 8192
INTERPRETER ?= NORMAL

CFLAGS += -DBENCH_ITERATIONS=$(ITERATIONS)

ifeq ($(INTERPRETER),FAST)
	export WAMR_CONFIG=$(realpath ./fast_interpreter_config.cmake)
else ifeq ($(INTERPRETER),NORMAL)
	export WAMR_CONFIG=$(realpath ./normal_interpreter_config.cmake)
else 
	$(error "Unknown INTERPRETER type: $(INTERPRETER). Use FAST or NORMAL.")
endif
# Change this to 0 show compiler invocation lines by default:
QUIET ?= 1

# RIOT_TERMINAL ?= miniterm
#
all: benchmark.wasm

.PHONY: .FORCE

benchmark.wasm: .FORCE
	make -C wasm HEAP=$(HEAP) STACK=$(STACK) SCALE_FACTOR=$(SCALE_FACTOR) BENCHMARK=$(BENCHMARK_FILE) benchmark.wasm
	mv wasm/benchmark.wasm .

include $(RIOTBASE)/Makefile.include

include ../Makefile.include
