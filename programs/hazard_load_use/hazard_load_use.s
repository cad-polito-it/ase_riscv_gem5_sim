.section .data
.align 4
input_value: .word 41

# The text section contains the instructions that the CPU runs.
.section .text
# Make _start visible as the point where the program begins.
.globl _start
_start:
    # A load-use RAW hazard can remain even when ALU forwarding is enabled.
    la   x5, input_value
    lw   x6, 0(x5)
    addi x7, x6, 1
    add  x8, x7, x6

# The End block stops the program and returns control to the simulator.
End:
    li a0, 0
    li a7, 93
    ecall
