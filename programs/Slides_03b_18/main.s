# Add an optional .data section here.
.align 4
V1: .word 1,2,3,4,5,6,7,8,9,10
V2: .word 1,2,3,4,5,6,7,8,9,10
result: .space 40

# The text section contains the instructions that the CPU runs.
.section .text
# Make _start visible as the point where the program begins.
.globl _start
_start:

    # Write your RISC-V assembly here.
    la    x1, V1
    lw    x1,0(x1)
    la    x2, V2
    lw    x2,0(x2)  
    nop
    nop
    nop
    nop
    main:
    la x1, V1
    la x2, V2
    la x3, result
    addi x4, x0, 10 
    cycle:
    lw x5, 0(x1)
    lw x6, 0(x2)
    add x7, x5, x6
    sw x7, 0(x3)
    addi x1, x1, 4
    addi x2, x2, 4
    addi x3, x3, 4
    addi x4, x4, -1
    bnez x4, cycle
    nop
    

# The End block stops the program and returns control to the simulator.
End:
    li a0, 0
    li a7, 93
    ecall
