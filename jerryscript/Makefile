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
CFLAGS += -DTHREAD_STACKSIZE_MAIN=100092
endif

export JERRY_HEAP = 1000 # KiB
export JERRY_STACK = 512 # KiB

# Add the package for Jerryscript
USEPKG += jerryscript

# generate .js.h header files of .js files
BLOBS += $(wildcard *.js)

include $(RIOTBASE)/Makefile.include
