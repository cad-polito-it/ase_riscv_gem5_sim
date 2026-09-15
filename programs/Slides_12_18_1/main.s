# Add an optional .data section here.
.section .data
.align 4
V1: .word 0,1,2,3,4,5,6,7,8,9
    
     
# The text section contains the instructions that the CPU runs.
.section .text
# Make _start visible as the point where the program begins.
.globl _start
_start:

        main: 
    la   x1, V1
    addi x3, x0, 3

Loop:
    lw   x2, 0(x1)
    addi x2, x2, 1
    sw   x2, 0(x1)
    addi x1, x1, 4
    bne  x2, x3, Loop


# The End block stops the program and returns control to the simulator.
End:
    li a0, 0
    li a7, 93
    ecall
