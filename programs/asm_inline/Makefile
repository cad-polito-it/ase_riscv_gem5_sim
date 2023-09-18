# tool macros
CC ?= gcc
CXX ?= # FILL: the compiler
CFLAGS := -O2 -march=rv64gc -mabi=lp64d -static -Wall -Wextra -D_GEM5_ -I$$GEM5_SRC/include -nostartfiles -nostdlib
CXXFLAGS := -O2 -static -Wall -Wextra 
COBJFLAGS := $(CFLAGS) -c

# path macros
OBJ_PATH := obj
SRC_PATH := .

# compile macros
TARGET_NAME = $$program
ifeq ($(OS),Windows_NT)
	TARGET_NAME := $(addsuffix .exe,$(TARGET_NAME))
endif
TARGET = $$program.elf
# src files & obj files
SRC := $(foreach x, $(SRC_PATH), $(wildcard $(addprefix $(x)/*,.c*)))

## NOTE: since we are compiling the code with static (otherwise we could use -lm5 for including the static compiled library of m5op )
ASM = $$GEM5_SRC/util/m5/src/abi/riscv/m5op.S
 
OBJ := $(addprefix $(OBJ_PATH)/, $(addsuffix .o, $(notdir $(basename $(SRC)))))


# clean files list
DISTCLEAN_LIST := $(OBJ) 
CLEAN_LIST := $(TARGET) \
			  $(DISTCLEAN_LIST)

# default rule
default: makedir all

# non-phony targets
$(TARGET): $(OBJ)
	$(CC) -o $@  -X ${ASM} $(OBJ)  $(CFLAGS) 

$(OBJ_PATH)/%.o: $(SRC_PATH)/%.c*
	$(CC) $(COBJFLAGS) -o $@ $<

# phony rules
.PHONY: makedir
makedir:
	@mkdir -p  $(OBJ_PATH) 

.PHONY: all
all: $(TARGET)

.PHONY: clean
clean:
	@echo CLEAN $(CLEAN_LIST)
	@rm -f $(CLEAN_LIST)

.PHONY: distclean
distclean:
	@echo CLEAN $(DISTCLEAN_LIST)
	@rm -f $(DISTCLEAN_LIST)
