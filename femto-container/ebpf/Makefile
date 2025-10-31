RIOTBASE ?= $(CURDIR)/../../RIOT

export EXTRA_CFLAGS += -Os -emit-llvm -DSCALE_FACTOR=$(SCALE_FACTOR)

include $(RIOTBASE)/makefiles/rbpf.inc.mk

.PHONY: all

# Default FILE to ../benchmark (so dump uses ../benchmark.bin by default)
DUMP_FILE ?= ../benchmark

dump:
	$(RBPF_GENRBF) dump $(DUMP_FILE).bin