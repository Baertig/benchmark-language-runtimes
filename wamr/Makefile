# name of your application
APPLICATION = wamr-benchmark

# Change this to your board if you want to build for a different board
BOARD ?= native

# This has to be the absolute path to the RIOT base directory:
RIOTBASE ?= $(CURDIR)/../RIOT

USEPKG += wamr
USEMODULE += ztimer_usec

# Select which benchmark to compile
BENCHMARK ?= tarfind
BENCHMARK_FILE = $(BENCHMARK).c

# Pass the benchmark name to the preprocessor and wasm build
CFLAGS += -DBENCHMARK=$(BENCHMARK_FILE)

ifeq (,$(filter native native32 native64,$(BOARD)))
CFLAGS += -DTHREAD_STACKSIZE_MAIN='(6 * 1024)'
endif

BLOBS += main.wasm

# Comment this out to disable code in RIOT that does safety checking
# which is not needed in a production environment but helps in the
# development process:
DEVELHELP ?= 1

# Change this to 0 show compiler invocation lines by default:
QUIET ?= 1

# RIOT_TERMINAL ?= miniterm
#
all: main.wasm

main.wasm: wasm/main.c wasm/Makefile
	make -C wasm BENCHMARK=$(BENCHMARK_FILE) main.wasm
	mv wasm/main.wasm .

include $(RIOTBASE)/Makefile.include
