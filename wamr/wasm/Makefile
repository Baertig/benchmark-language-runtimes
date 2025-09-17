# CLANG ?= /opt/wasi-sdk/bin/clang
CLANG ?= clang
TARGET ?= wasm32-unknown-unknown

LINK_FLAGS := -z,stack-size=4096 \
		--export=main \
		--allow-undefined \
		--export=__heap_base \
		--export=__data_end \
		--strip-all \
		--export-dynamic \
		-error-limit=0 \
		--lto-O3 \
		-O3 \
		--gc-sections\
		--initial-memory=65536 \
		--no-entry \

# Map LINK_FLAGS for use with the clang driver (-Wl, passes args to the linker)
comma := ,
WLINK_FLAGS := $(addprefix -Wl$(comma),$(LINK_FLAGS))

# Find compiler-rt builtins for wasm32 (needed for __multi3, etc.)
RESOURCE_DIR := $(shell $(CLANG) --print-resource-dir)
BUILTINS := $(firstword $(wildcard \
    $(RESOURCE_DIR)/lib/wasm32/libclang_rt.builtins-wasm32.a \
    $(RESOURCE_DIR)/lib/wasi/libclang_rt.builtins-wasm32.a \
    $(RESOURCE_DIR)/lib/libclang_rt.builtins-wasm32.a))

# --initial-memory may only be set in 64kB steps (pagesize of WASM)
# even though this one page is 64kB
#	- data starts at 0, (1024 is chosen by lld)
#	- stack starts at 4kB growing down
#	- heap at 4kB growing up (see stack-size option)
#	-> memory can be smaller than first page
# without stack-size option stack will start at 64kB
#	-> heap needs a second page
# wasm-ld 8 and 11 do not need --initial-memory=64kB
GLOBAL_SCALE_FACTOR ?= 1

COMPILE_FLAGS := -Wall \
		-Os \
		-flto \
		-fvisibility=hidden \
		-ffunction-sections \
		-fdata-sections \
		-nostdlib \
		-DGLOBAL_SCALE_FACTOR=1 \

%.show: %.wasm
	wasm2wat $<

%.wasm: %.o Makefile
	$(CLANG) --target=$(TARGET) -nostdlib \
		-o $@ \
		$< \
		$(WLINK_FLAGS) \
		$(BUILTINS)

%.o: %.c Makefile
	$(CLANG) --target=$(TARGET) -ffreestanding -fno-builtin \
		-c \
		$(COMPILE_FLAGS) \
		-o $@ \
		$<

%.wat: %.wasm Makefile
	wasm2wat -o $@ $<

.PHONY: .FORCE

benchmark.wasm: COMPILE_FLAGS += -include $(BENCHMARK)
benchmark.wasm: $(BENCHMARK) benchmark.c .FORCE
