APPLICATION = lua_benchmark

# If no BOARD is found in the environment, use this default:
BOARD ?= native

# This has to be the absolute path to the RIOT base directory:
RIOTBASE ?= $(CURDIR)/../RIOT

# Comment this out to disable code in RIOT that does safety checking
# which is not needed in a production environment but helps in the
# development process:
DEVELHELP ?= 1

# Change this to 0 show compiler invocation lines by default:
QUIET ?= 1

ifeq (,$(filter native native32 native64,$(BOARD)))
  # This stack size is large enough to run Lua print() functions of
  # various lengths. Other functions untested.
  CFLAGS += -DTHREAD_STACKSIZE_MAIN='(THREAD_STACKSIZE_DEFAULT+2048)'
endif

USEPKG += lua

USEMODULE += ztimer_usec

# generate .lua.h header files of .lua files
BENCHMARK ?= tarfind
BENCHMARK_FILE = benchmarks/$(BENCHMARK).lua
ITERATIONS ?= 1
SCALE_FACTOR ?= 1
MEM_STATS ?= OFF
GC_AGGRESSIVE ?= OFF

CFLAGS += -DBENCH_ITERATIONS=$(ITERATIONS)
HEAP ?= 204800

CFLAGS += -DLUA_MEM_SIZE=$(HEAP)

ifeq ($(MEM_STATS), ON)
  CFLAGS += -DMEM_STATS
endif

ifeq ($(GC_AGGRESSIVE), ON)
  CFLAGS += -DGC_AGGRESSIVE
endif

all: benchmark.lua

.PHONY: .FORCE

benchmark.lua: .FORCE
	cp $(BENCHMARK_FILE) benchmark.lua
	sed -i "s/SCALE_FACTOR = .*/SCALE_FACTOR = $(SCALE_FACTOR);/" benchmark.lua
	@grep "SCALE_FACTOR =" benchmark.lua

BLOBS += benchmark.lua

include $(RIOTBASE)/Makefile.include

include ../Makefile.include
