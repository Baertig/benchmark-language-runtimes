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

BLOBS += ebpf/crc_32.bin

CFLAGS += -DFEMTO_CONTAINER_BRANCHES_ALLOWED=2000000


include $(RIOTBASE)/Makefile.include

include ../Makefile.include