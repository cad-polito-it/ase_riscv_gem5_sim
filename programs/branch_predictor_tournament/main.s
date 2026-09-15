# Add an optional .data section here.
.section .data
.align 4
prediction_score: .word 0

# The text section contains the instructions that the CPU runs.
.section .text
# Make _start visible as the point where the program begins.
.globl _start
_start:
    li x1, 96
    li x2, 0
    li x3, 0

# This workload combines alternating, biased, correlated, and loop branches.
PredictorTest:
    # Alternating branch: taken, not taken, taken, not taken, ...
    xori x2, x2, 1
    beq  x2, x0, AlternatingTaken
    addi x3, x3, 1
    j    AlternatingDone
AlternatingTaken:
    addi x3, x3, 2
AlternatingDone:

    # Biased branch: taken in seven out of every eight iterations.
    andi x4, x1, 7
    bne  x4, x0, BiasedTaken
    addi x3, x3, 4
    j    BiasedDone
BiasedTaken:
    addi x3, x3, 8
BiasedDone:

    # The second branch has the same outcome as the first correlated branch.
    andi x5, x1, 1
    beq  x5, x0, CorrelationFirstTaken
    li   x6, 0
    j    CorrelationFirstDone
CorrelationFirstTaken:
    li   x6, 1
CorrelationFirstDone:
    bne  x6, x0, CorrelationSecondTaken
    addi x3, x3, 16
    j    CorrelationSecondDone
CorrelationSecondTaken:
    addi x3, x3, 32
CorrelationSecondDone:

    # Rare branch: taken once every sixteen iterations.
    andi  x7, x1, 15
    sltiu x8, x7, 1
    bne   x8, x0, RareTaken
    addi  x3, x3, 64
    j     RareDone
RareTaken:
    addi x3, x3, 128
RareDone:

    addi x1, x1, -1
    bnez x1, PredictorTest

    la x9, prediction_score
    sw x3, 0(x9)

# The End block stops the program and returns control to the simulator.
End:
    li a0, 0
    li a7, 93
    ecall
