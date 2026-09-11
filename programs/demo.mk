CC ?= gcc
OBJDUMP ?= objdump
CFLAGS := $$OPTIMIZATION_FLAGS -mcmodel=medlow -march=rv32imf -mabi=ilp32 -mno-relax -Wall -Wextra -nostartfiles
TARGET = $$program.elf

all: $(TARGET) $$program.dump

$(TARGET): $(ASM)
	$(CC) -o $@ $(ASM) $(CFLAGS)

$$program.dump: $(TARGET)
	$(OBJDUMP) -d $< > $@

clean:
	rm -f $(TARGET) $$program.dump
