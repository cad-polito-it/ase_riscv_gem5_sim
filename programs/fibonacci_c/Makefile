# tool macros
CC ?= gcc
CXX ?= g++
OBJDUMP ?= objdump
CFLAGS :=  $$OPTIMIZATION_FLAGS -mcmodel=medlow -march=rv32imf -mabi=ilp32 -mno-relax -Wall -Wextra  -nostartfiles -T./linker.ld 
CXXFLAGS := $$OPTIMIZATION_FLAGS -static -Wall -Wextra 
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

ASM =  ./crt0.S 

OBJ := $(addprefix $(OBJ_PATH)/, $(addsuffix .o, $(notdir $(basename $(SRC)))))


# clean files list
DISTCLEAN_LIST := $(OBJ) 
CLEAN_LIST := $(TARGET) \
			  $(DISTCLEAN_LIST)

# default rule
default: makedir all

# non-phony targets
$(TARGET): $(OBJ)
	$(CC) -o $@  ${ASM} $(OBJ)  $(CFLAGS) 

$(OBJ_PATH)/%.o: $(SRC_PATH)/%.c*
	$(CC) $(COBJFLAGS) -o $@ $<

$(TARGET_NAME).dump: $(TARGET)
	$(OBJDUMP) -d $< > $@

# phony rules
.PHONY: makedir
makedir:
	@mkdir -p  $(OBJ_PATH) 

.PHONY: all
all: $(TARGET) $(TARGET_NAME).dump

.PHONY: clean
clean:
	@echo CLEAN $(CLEAN_LIST)
	@rm -f $(CLEAN_LIST)

.PHONY: distclean
distclean:
	@echo CLEAN $(DISTCLEAN_LIST)
	@rm -f $(DISTCLEAN_LIST)
