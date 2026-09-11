.section .data
.balign 64
line_a: .word 11
.space 60
line_b: .word 22
.space 60
line_c: .word 33

# The text section contains the instructions that the CPU runs.
.section .text
# Make _start visible as the point where the program begins.
.globl _start
_start:
    # First accesses miss in L1; the repeated line_a access demonstrates a hit.
    la  x5, line_a
    lw  x6, 0(x5)
    la  x7, line_b
    lw  x8, 0(x7)
    la  x9, line_c
    lw  x10, 0(x9)
    lw  x11, 0(x5)
    add x12, x6, x8
    add x13, x12, x10

# The End block stops the program and returns control to the simulator.
End:
    li a0, 0
    li a7, 93
    ecall
