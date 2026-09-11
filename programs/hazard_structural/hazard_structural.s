# The text section contains the instructions that the CPU runs.
.section .text
# Make _start visible as the point where the program begins.
.globl _start
_start:
    # Two independent divides compete for the single non-pipelined FP divider.
    li      x5, 0x40800000
    li      x6, 0x40000000
    fmv.w.x f0, x5
    fmv.w.x f1, x6
    fdiv.s  f2, f0, f1
    fdiv.s  f3, f0, f1
    fadd.s  f4, f2, f3

# The End block stops the program and returns control to the simulator.
End:
    li a0, 0
    li a7, 93
    ecall
