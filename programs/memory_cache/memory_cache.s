.section .data
.balign 64
line_a: .word 11, 12
.space 56
line_b: .word 22
.space 60
line_c: .word 33
.space 60

# The text section contains the instructions that the CPU runs.
.section .text
# Make _start visible as the point where the program begins.
.globl _start
.balign 64
_start:
    # Run twice: the first pass fills the caches and the second reuses them.
    li  x20, 0
    li  x21, 2
cache_demo:
    la  x5, line_a
    lw  x6, 0(x5)        # First pass: D$ miss.
    nop                   # Separate the next access from the miss response.
    lw  x14, 4(x5)       # Same line: spatial D$ hit.
    la  x7, line_b
    lw  x8, 0(x7)        # Different line: D$ miss.
    la  x9, line_c
    lw  x10, 0(x9)       # Another different line: D$ miss.
    nop
    lw  x11, 0(x5)       # Repeated line: temporal D$ hit.
    add x12, x6, x8
    add x13, x12, x10
    addi x20, x20, 1
    blt x20, x21, cache_demo  # Taken branch revisits cached instruction lines.

# The End block stops the program and returns control to the simulator.
End:
    li a0, 0
    li a7, 93
    ecall
