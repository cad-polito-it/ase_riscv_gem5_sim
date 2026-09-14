.section .data

inputs:  .float 6.8, 2.1
results: .float 0.0, 0.0, 0.0

# The text section contains the instructions that the CPU runs.
.section .text
# Make _start visible as the point where the program begins.
.globl _start
_start:

    # The three FP operations use different configured unit latencies.
    la     x5, inputs
    flw    f1, 0(x5)
    flw    f2, 4(x5)
    fadd.s f3, f1, f2
    fmul.s f4, f1, f2
    fdiv.s f5, f1, f2
    fadd.s f3, f1, f2

    la     x6, results
    fsw    f3, 0(x6)
    fsw    f4, 4(x6)
    fsw    f5, 8(x6)

# The End block stops the program and returns control to the simulator.
End:
    li a0, 0
    li a7, 93
    ecall
