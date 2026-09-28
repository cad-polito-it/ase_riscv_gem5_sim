CC ?= gcc
OBJDUMP ?= objdump
ASE_RISCV_MARCH ?= rv32imafd_zicsr_zifencei
CFLAGS := $$OPTIMIZATION_FLAGS -mcmodel=medlow -march=$(ASE_RISCV_MARCH) -mabi=ilp32 -mno-relax -Wall -Wextra -nostdlib
TARGET = $$program.elf

all: $(TARGET) $$program.dump

$(TARGET): $(ASM)
	$(CC) -o $@ $(ASM) $(CFLAGS)

$$program.dump: $(TARGET)
	$(OBJDUMP) -d $< > $@

clean:
	rm -f $(TARGET) $$program.dump
