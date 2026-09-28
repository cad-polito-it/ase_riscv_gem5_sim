.section .data
counter:   .word 3
values:    .word 10, 20, 0
unchanged: .word 99

# The text section contains the instructions that the CPU runs.
.section .text
# Make _start visible as the point where the program begins.
.globl _start
_start:

    la   x5, counter
    lw   x6, 0(x5)
    addi x6, x6, 1
    sw   x6, 0(x5)

    la   x7, values
    lw   x8, 0(x7)
    lw   x9, 4(x7)
    add  x10, x8, x9
    sw   x10, 8(x7)

# The End block stops the program and returns control to the simulator.
End:
    li a0, 0
    li a7, 93
    ecall
