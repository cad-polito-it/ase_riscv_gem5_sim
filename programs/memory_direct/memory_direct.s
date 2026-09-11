.section .data
.align 4
values: .word 10, 20, 0

# The text section contains the instructions that the CPU runs.
.section .text
# Make _start visible as the point where the program begins.
.globl _start
_start:
    # Direct memory exposes fixed instruction, load, and store latencies.
    la  x5, values
    lw  x6, 0(x5)
    lw  x7, 4(x5)
    add x8, x6, x7
    sw  x8, 8(x5)

# The End block stops the program and returns control to the simulator.
End:
    li a0, 0
    li a7, 93
    ecall
