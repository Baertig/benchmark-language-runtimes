# application name
APPLICATION = femto-container_benchmark

# default BOARD environment
BOARD ?= native

# This has to be the absolute path to the RIOT base directory:
RIOTBASE ?= $(CURDIR)/../RIOT

# Comment this out to disable code in RIOT that does safety checking
# which is not needed in a production environment but helps in the
# development process:
DEVELHELP ?= 1

USEMODULE += ztimer_usec
USEPKG += femto-container

BENCHMARK ?= crc_32
BENCHMARK_FILE = $(CURDIR)/ebpf/$(BENCHMARK).c
ITERATIONS ?= 1

BLOBS += benchmark.bin
export SCALE_FACTOR ?= 1

ifeq ($(BENCHMARK), crc_32)
    BENCHMARK_ID = 1
else ifeq ($(BENCHMARK), libud)
    BENCHMARK_ID = 2
else ifeq ($(BENCHMARK), xgboost)
	BENCHMARK_ID = 3
else 
	$(error "Unsupported BENCHMARK: $(BENCHMARK)")
endif

CFLAGS += -DFEMTO_CONTAINER_BRANCHES_ALLOWED=2000000 
CFLAGS += -DBENCHMARK_ID=$(BENCHMARK_ID)
CFLAGS += -DBENCH_ITERATIONS=$(ITERATIONS)

all: $(BLOBS)

.PHONY: benchmark.bin
benchmark.bin: $(BENCHMARK_FILE)
	$(MAKE) -C $(CURDIR)/ebpf all RBPF_SOURCES=$(BENCHMARK_FILE)
	cp $(CURDIR)/ebpf/$(BENCHMARK).bin $(CURDIR)/benchmark.bin
# TODO: Remove (currently the makefile from ebpf build all the .c file , However I used different SCALE_FACTOR per benchmark)
# this means, that I have to recompiler for every run and cannot keep intermediary .bin / .o files
	rm $(CURDIR)/ebpf/*.bin
	rm $(CURDIR)/ebpf/*.o

.PHONY: clean-ebpf
clean-ebpf:
	$(MAKE) -C $(CURDIR)/ebpf clean

clean: clean-ebpf

include $(RIOTBASE)/Makefile.include

include ../Makefile.include