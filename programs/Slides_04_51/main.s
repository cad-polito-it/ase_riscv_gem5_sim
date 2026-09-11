# Add an optional .data section here.
.align 4
V1: .word 0,1,2,3,4,5,6,7,8,9

# The text section contains the instructions that the CPU runs.
.section .text
# Make _start visible as the point where the program begins.
.globl _start
_start:

    # Write your RISC-V assembly here.
    la    x2, V1
    lw    x1,0(x2)
    sub   x4,x1,x5
    and   x6,x1,x7
    or    x8,x1,x9    

# The End block stops the program and returns control to the simulator.
End:
    li a0, 0
    li a7, 93
    ecall
