.section .data
.align 4
V1: .word 0,1,2,3,4,5,6,7,8,9
V2: .word 0,1,2,3,4,5,6,7,8,9
V3: .word 0,1,2,3,4,5,6,7,8,9
V4: .word 0,1,2,3,4,5,6,7,8,9
     V5: .word 0,1,2,3,4,5,6,7,8,9


# The text section contains the instructions that the CPU runs.
.section .text
# Make _start visible as the point where the program begins.
.globl _start
_start:
    # Direct memory with all latencies set to 1 adds no memory wait cycles.
        main: 
  addi  x6, x0, 90
  la  x1, V1
  la  x2, V2
  la  x3, V3
  la  x4, V4
  la  x5, V5
loop:  
  flw  f1, 0(x1)
  flw  f2, 0(x2)
  fdiv.s f4, f1, f2
  flw  f3, 0(x3)
  fadd.s f4, f4, f3 

    fsw  f4, 0(x4)
  fmul.s  f4, f1, f3
  fsw   f4, 0(x5) 
  addi  x1, x1, 4
  addi  x2, x2, 4
  addi  x3, x3, 4
  addi  x4, x4, 4
  addi  x5, x5, 4
  addi  x6, x6, -1
  bnez  x6, loop  
  nop            
    
# The End block stops the program and returns control to the simulator.
End:
    li a0, 0
    li a7, 93
    ecall
