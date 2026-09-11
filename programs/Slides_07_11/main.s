# Add an optional .data section here.
.section .data
Val_A: .word 10
Val_B: .word 20
Val_C: .word 10
Val_D: .word 20
Val_R1: .word 0 
Val_R2: .word 0 

# The text section contains the instructions that the CPU runs.
.section .text
# Make _start visible as the point where the program begins.
.globl _start
_start:

    # Write your RISC-V assembly here.
    la    x10, Val_A
    la    x11, Val_B
    la    x12, Val_C
    la    x13, Val_D
    la    x14, Val_R1
    la    x15, Val_R2
    
main:    
    lw    x1,0(x10)
    lw    x2,0(x11)
    lw    x3,0(x12)
    add   x5, x1, x2
    lw    x4,0(x13)
    sw    x5,0(x14)
    add   x6, x3, x4
    sw    x6,0(x15)

# The End block stops the program and returns control to the simulator.
End:
    li a0, 0
    li a7, 93
    ecall
