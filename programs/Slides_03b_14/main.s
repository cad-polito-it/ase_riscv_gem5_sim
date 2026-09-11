# Add an optional .data section here.
.section .data
Val_A: .word 10
Val_B: .word 20
Val_C: .word 0 

# The text section contains the instructions that the CPU runs.
.section .text
# Make _start visible as the point where the program begins.
.globl _start
_start:

    # Write your RISC-V assembly here.
    la    x1, Val_A
    lw    x1,0(x1)
    la    x2, Val_B
    lw    x2,0(x2)
    add   x3, x2, x1
    la    x4, Val_C
    sw    x3,0(x4)   

# The End block stops the program and returns control to the simulator.
End:
    li a0, 0
    li a7, 93
    ecall
