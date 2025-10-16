# application name
APPLICATION = femtocontainer_benchmark

# default BOARD environment
BOARD ?= native

# This has to be the absolute path to the RIOT base directory:
RIOTBASE ?= $(CURDIR)/../RIOT

# Comment this out to disable code in RIOT that does safety checking
# which is not needed in a production environment but helps in the
# development process:
DEVELHELP ?= 1

USEPKG += femto-container

BENCHMARK ?= crc_32
BENCHMARK_FILE = $(BENCHMARK).c

BLOBS += ebpf/$(BENCHMARK).bin

CFLAGS += -DFEMTO_CONTAINER_BRANCHES_ALLOWED=2000000

all: $(BLOBS)

ebpf/%.bin: ebpf/%.c ebpf/%.o
	$(MAKE) -C ebpf all

.PHONY: clean-ebpf
clean-ebpf:
	$(MAKE) -C ebpf clean

clean: clean-ebpf

include $(RIOTBASE)/Makefile.include

include ../Makefile.include