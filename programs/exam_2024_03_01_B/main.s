# Add an optional .data section here.
.data
V1: .double 0,1,2,3,4,5,6,7,8
V2: .double 0,1,2,3,4,5,6,7,8
V3: .double 0,1,2,3,4,5,6,7,8
V4: .double 0,1,2,3,4,5,6,7,8
V5: .double 0,1,2,3,4,5,6,7,8

# The text section contains the instructions that the CPU runs.
.section .text
# Make _start visible as the point where the program begins.
.globl _start
_start:

    main: 
    addi x6, x0, 10 
    la x1, V1 
    la x2, V2 
    la x3, V3 
    la x4, V4 
    la x5, V5 
     
loop:
    fld f1, 0(x1)
    fld f2, 0(x2)
    fld f3, 0(x3)
    fld f4, 0(x4)

    fdiv.d f5, f1, f2
    fdiv.d f6, f3, f4
    fadd.d f7, f6, f5

    fsd f7, 0(x5)

    addi x1, x1, 8
    addi x2, x2, 8
    addi x3, x3, 8
    addi x4, x4, 8
    addi x5, x5, 8

    addi x6, x6, -1

    bnez x6, loop

    nop

# The End block stops the program and returns control to the simulator.
End:
    li a0, 0
    li a7, 93
    ecall
