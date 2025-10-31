RIOTBASE ?= $(CURDIR)/../../RIOT

export EXTRA_CFLAGS += -Os -emit-llvm -DSCALE_FACTOR=$(SCALE_FACTOR)

include $(RIOTBASE)/makefiles/rbpf.inc.mk

.PHONY: all

dump:
	$(RBPF_GENRBF) dump ../benchmark.bin

dump-crc_32:
	$(RBPF_GENRBF) dump crc_32.bin

dump-libud:
	$(RBPF_GENRBF) dump libud.bin