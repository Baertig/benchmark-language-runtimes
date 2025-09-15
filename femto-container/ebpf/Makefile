RIOTBASE ?= $(CURDIR)/../../RIOT

export EXTRA_CFLAGS += -Os -emit-llvm -DGLOBAL_SCALE_FACTOR=1

include $(RIOTBASE)/makefiles/rbpf.inc.mk

dump:
	$(RBPF_GENRBF) dump crc_32.bin