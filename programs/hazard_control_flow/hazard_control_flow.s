# The text section contains the instructions that the CPU runs.
.section .text
# Make _start visible as the point where the program begins.
.globl _start
_start:
    # The taken branch creates a backward control-flow arrow on each iteration.
    addi x5, x0, 0
    addi x6, x0, 4
Loop:
    addi x5, x5, 1
    blt  x5, x6, Loop
    addi x7, x5, 10
    nop

# The End block stops the program and returns control to the simulator.
End:
    li a0, 0
    li a7, 93
    ecall
