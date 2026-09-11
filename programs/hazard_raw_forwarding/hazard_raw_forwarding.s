# The text section contains the instructions that the CPU runs.
.section .text
# Make _start visible as the point where the program begins.
.globl _start
_start:
    # Each instruction reads the result immediately before it.
    addi x5, x0, 2
    addi x6, x5, 3
    add  x7, x6, x5
    sub  x8, x7, x6

# The End block stops the program and returns control to the simulator.
End:
    li a0, 0
    li a7, 93
    ecall
