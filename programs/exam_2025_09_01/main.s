# Add an optional .data section here.
.section .data
.align 4
V1: .word 0,1,2,3,4,5,6,7,8,9
V2: .word 0,1,2,3,4,5,6,7,8,9
V3: .word 0,1,2,3,4,5,6,7,8,9
V4: .word 0,1,2,3,4,5,6,7,8,9
     V5: .word 0,1,2,3,4,5,6,7,8,9
V6: .word 0,1,2,3,4,5,6,7,8,9     
     
# The text section contains the instructions that the CPU runs.
.section .text
# Make _start visible as the point where the program begins.
.globl _start
_start:

        main: 
    addi x7, x0, 10 
    la x1, V1 
    la x2, V2 
    la x3, V3 
    la x4, V4 
    la x5, V5 
    la x6, V6
     
loop:
    flw f1, 0(x1)
    flw f2, 0(x2)
    fadd.s f4, f1, f2 
    flw f3, 0(x3)
    fsw f4, 0(x4) 
    fmul.s f5,f2,f3
    fsw f5, 0(x5)
    fdiv.s f6, f1, f3
    fsw f6, 0(x6)

    addi x1, x1, 4
    addi x2, x2, 4 
    addi x3, x3, 4 
    addi x4, x4, 4 
    addi x5, x5, 4 
    addi x6, x6, 4 
    addi x7, x7, -1 
    bnez x7, loop
    nop

# The End block stops the program and returns control to the simulator.
End:
    li a0, 0
    li a7, 93
    ecall
