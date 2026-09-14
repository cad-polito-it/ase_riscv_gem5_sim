# RV32G teaching demo: representative I, M, F, D, Zicsr and Zifencei instructions.

.section .data
.balign 8
integers:      .word 18, 5
single_values: .float 6.0, 2.0
double_values: .double 9.0, 3.0
results:       .space 64

# The text section contains the instructions that the CPU runs.
.section .text
# Make _start visible as the point where the program begins.
.globl _start
_start:
    # RV32I: integer arithmetic, shifts, comparisons, and memory access.
    la    x5, integers
    lw    x6, 0(x5)
    lw    x7, 4(x5)
    add   x8, x6, x7
    sub   x9, x6, x7
    sll   x10, x6, x7
    slt   x11, x7, x6
    sltu  x12, x7, x6
    xor   x13, x6, x7
    srl   x14, x6, x7
    sra   x15, x6, x7
    or    x16, x6, x7
    and   x17, x6, x7
    addi  x18, x6, 7
    slti  x19, x7, 8
    sltiu x20, x7, 8
    xori  x21, x6, 3
    ori   x22, x6, 3
    andi  x23, x6, 15
    slli  x24, x7, 2
    srli  x25, x6, 1
    srai  x26, x6, 1
    lui   x27, 0x12
    auipc x28, 0

    la    x5, results
    sb    x8, 0(x5)
    sh    x9, 2(x5)
    sw    x13, 4(x5)
    lb    x8, 0(x5)
    lbu   x9, 0(x5)
    lh    x10, 2(x5)
    lhu   x11, 2(x5)

    # RV32M: multiply and divide variants.
    mul    x8, x6, x7
    mulh   x9, x6, x7
    mulhsu x10, x6, x7
    mulhu  x11, x6, x7
    div    x12, x6, x7
    divu   x13, x6, x7
    rem    x14, x6, x7
    remu   x15, x6, x7

    # RV32I control flow: all conditional branch forms, JAL, and JALR.
    beq  x6, x6, branch_ne
    nop
branch_ne:
    bne  x6, x7, branch_lt
    nop
branch_lt:
    blt  x6, x7, branch_ge
branch_ge:
    bge  x7, x6, branch_ltu
branch_ltu:
    bltu x6, x7, branch_geu
branch_geu:
    bgeu x7, x6, call_demo
call_demo:
    jal  x0, after_call
    nop
after_call:
    la   x28, indirect_target
    nop
    nop
    nop
    jalr x0, 0(x28)
    nop
indirect_target:
    j floating_demo

floating_demo:
    # RV32F: single-precision arithmetic, comparison, conversion, and transfer.
    la      x5, single_values
    flw     f0, 0(x5)
    flw     f1, 4(x5)
    fadd.s  f2, f0, f1
    fsub.s  f3, f0, f1
    fmul.s  f4, f0, f1
    fdiv.s  f5, f0, f1
    fsqrt.s f6, f0
    fsgnj.s f7, f0, f1
    fsgnjn.s f8, f0, f1
    fsgnjx.s f9, f0, f1
    fmin.s  f10, f0, f1
    fmax.s  f11, f0, f1
    feq.s   x10, f0, f1
    flt.s   x11, f1, f0
    fle.s   x12, f1, f0
    fclass.s x13, f0
    fcvt.w.s x14, f0, rtz
    fcvt.wu.s x15, f0, rtz
    fcvt.s.w f12, x6
    fcvt.s.wu f13, x7
    fmv.x.w x16, f0
    fmv.w.x f14, x16

    # RV32D: double-precision operations and F/D conversions.
    la      x5, double_values
    fld     f16, 0(x5)
    fld     f17, 8(x5)
    fadd.d  f18, f16, f17
    fsub.d  f19, f16, f17
    fmul.d  f20, f16, f17
    fdiv.d  f21, f16, f17
    fsqrt.d f22, f16
    fsgnj.d f23, f16, f17
    fsgnjn.d f24, f16, f17
    fsgnjx.d f25, f16, f17
    fmin.d  f26, f16, f17
    fmax.d  f27, f16, f17
    feq.d   x18, f16, f17
    flt.d   x19, f17, f16
    fle.d   x20, f17, f16
    fclass.d x21, f16
    fcvt.w.d x22, f16, rtz
    fcvt.wu.d x23, f16, rtz
    fcvt.d.w f28, x6
    fcvt.d.wu f29, x7
    fcvt.s.d f30, f16
    fcvt.d.s f31, f0

    la  x5, results
    fsw f2, 8(x5)
    fsd f18, 16(x5)

    # Zicsr and Zifencei operations included by the G profile.
    csrrs x24, fcsr, x0
    fence
    fence.i

# The End block stops the program and returns control to the simulator.
End:
    li a0, 0
    li a7, 93
    ecall
