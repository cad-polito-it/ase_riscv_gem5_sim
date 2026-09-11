CC ?= gcc
OBJDUMP ?= objdump
CFLAGS := $$OPTIMIZATION_FLAGS -mcmodel=medlow -march=rv32imf -mabi=ilp32 -mno-relax -Wall -Wextra -nostdlib
TARGET = $$program.elf
ASM = ./main.s
all:
	$(CC) -o $(TARGET) $(ASM) $(CFLAGS)
	$(OBJDUMP) -d $(TARGET) > $$program.dump
clean:
	rm -f $(TARGET) $$program.dump
