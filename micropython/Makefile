# name of your application
APPLICATION = micropython

# If no BOARD is found in the environment, use this default:
BOARD ?= native

# This has to be the absolute path to the RIOT base directory:
RIOTBASE ?= $(CURDIR)/../RIOT

# select MicroPython package
USEPKG += micropython
USEMODULE += ztimer_usec

# include boot.py as header
BLOBS += tarfind.py

# configure MicroPython's heap size
MP_RIOT_HEAPSIZE ?= $(shell echo $$((32 * 1024)))

# MicroPython needs a larger stack
CFLAGS += '-DTHREAD_STACKSIZE_MAIN=THREAD_STACKSIZE_DEFAULT*4'

# use miniterm (instead of the default pyterm) in order to support control
# characters (CTRL-D ...)
RIOT_TERMINAL ?= miniterm

include $(RIOTBASE)/Makefile.include
