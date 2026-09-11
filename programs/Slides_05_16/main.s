# Add an optional .data section here.
.section .data
Val: .word 10

# The text section contains the instructions that the CPU runs.
.section .text
# Make _start visible as the point where the program begins.
.globl _start
_start:

    # Write your RISC-V assembly here.
    la    x1, Val
    flw   f1,0(x1)
    fmul.s f0, f4, f6
    nop
    nop
    fadd.s f2, f4, f6
    nop
    nop
    flw f2, 0(x1)   

# The End block stops the program and returns control to the simulator.
End:
    li a0, 0
    li a7, 93
    ecall
