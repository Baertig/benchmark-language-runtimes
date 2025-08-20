# name of your application
APPLICATION = native-benchmark

# Change this to your board if you want to build for a different board
BOARD ?= native

# This has to be the absolute path to the RIOT base directory:
RIOTBASE ?= $(CURDIR)/../RIOT

USEMODULE += ztimer_usec

# Select which benchmark to compile
BENCHMARK ?= tarfind
BENCHMARK_FILE = $(BENCHMARK).c

# Include the selected benchmark source file
SRC += benchmarks/$(BENCHMARK_FILE)
SRC += beebsc.c
SRC += main.c

# Comment this out to disable code in RIOT that does safety checking
# which is not needed in a production environment but helps in the
# development process:
DEVELHELP ?= 1
GLOBAL_SCALE_FACTOR ?= 1

CFLAGS += -DCONFIG_MAIN_EXIT_ON_RETURN=1
CFLAGS += -DGLOBAL_SCALE_FACTOR=$(GLOBAL_SCALE_FACTOR)

WERROR ?= 0
# Change this to 0 show compiler invocation lines by default:
QUIET ?= 1

include $(RIOTBASE)/Makefile.include