# Add an optional .data section here.
.section .data
vect1: .word 0,1,2,3,4,5,6,7,8,9
vect2: .word 0,1,2,3,4,5,6,7,8,9
vect3: .word 0,1,2,3,4,5,6,7,8,9
     
# The text section contains the instructions that the CPU runs.
.section .text
# Make _start visible as the point where the program begins.
.globl _start
_start:

        main: 
    addi x1, x0, 3 
    la x2, vect1 
    la x3, vect2 
    la x4, vect3 
     
loop:
    flw f1, 0(x2)
    flw f2, 0(x3)
    fmul.s f3, f1, f1 
    fdiv.s f4, f1, f2
    fadd.s f5, f3, f4
    fsw f5, 0(x4) 

    addi x2, x2, 4 
    addi x3, x3, 4 
    addi x4, x4, 4 
    addi x1, x1, -1 
    bnez x1, loop
   

# The End block stops the program and returns control to the simulator.
End:
    li a0, 0
    li a7, 93
    ecall
