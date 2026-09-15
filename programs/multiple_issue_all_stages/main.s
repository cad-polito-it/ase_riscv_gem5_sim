# Add an optional .data section here.
.section .data
.align 4
input_a: .float 2.0, 3.0
input_b: .float 4.0, 5.0
output:  .zero 8

# The text section contains the instructions that the CPU runs.
.section .text
# Make _start visible as the point where the program begins.
.globl _start
_start:
    la   x1, input_a
    la   x2, input_b
    la   x3, output
    li   x4, 2

# This loop demonstrates front-end, execution, memory, CDB, and commit stages.
Demo:
    flw    f1, 0(x1)
    flw    f2, 0(x2)
    fmul.s f3, f1, f2
    addi   x5, x0, 7
    fadd.s f4, f3, f1
    fsw    f4, 0(x3)
    addi   x1, x1, 4
    addi   x2, x2, 4
    addi   x3, x3, 4
    addi   x4, x4, -1
    bnez   x4, Demo

# The End block stops the program and returns control to the simulator.
End:
    li a0, 0
    li a7, 93
    ecall
