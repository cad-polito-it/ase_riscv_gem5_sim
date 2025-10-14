.data
    pi_result: .float 0.0
    sixteen: .float 16.0
    four: .float 4.0
    two: .float 2.0
    one: .float 1.0
    eight: .float 8.0
    
.text
.globl _start

_start:
    # BBP formula: π = Σ[k=0 to ∞] (1/16^k) * (4/(8k+1) - 2/(8k+4) - 1/(8k+5) - 1/(8k+6))
    
    flw f0, one, t0          # f0 = 1.0
    flw f1, sixteen, t0      # f1 = 16.0  
    flw f2, four, t0         # f2 = 4.0
    flw f3, two, t0          # f3 = 2.0
    flw f4, eight, t0        # f4 = 8.0
    
    fmv.s f10, f0            # f10 = running sum = 0
    fmv.s f11, f0            # f11 = 16^(-k), start with 1
    
    li t1, 50               # Number of terms (50 gives good precision)
    li t2, 0                # k counter
    
bbp_loop:
    beq t2, t1, bbp_finish
    
    # Convert k to float
    fcvt.s.w f12, t2        # f12 = k (float)
    
    # Calculate 8k
    fmul.s f13, f4, f12     # f13 = 8k
    
    # Calculate terms: 4/(8k+1), 2/(8k+4), 1/(8k+5), 1/(8k+6)
    fadd.s f14, f13, f0     # f14 = 8k+1
    fdiv.s f15, f2, f14     # f15 = 4/(8k+1)
    
    fadd.s f14, f13, f2     # f14 = 8k+4  
    fdiv.s f16, f3, f14     # f16 = 2/(8k+4)
    fsub.s f15, f15, f16    # f15 = 4/(8k+1) - 2/(8k+4)
    
    fadd.s f14, f13, f2     # f14 = 8k+5
    fadd.s f14, f14, f0     # f14 = 8k+5
    fdiv.s f16, f0, f14     # f16 = 1/(8k+5)
    fsub.s f15, f15, f16    # Subtract 1/(8k+5)
    
    fadd.s f14, f13, f2     # f14 = 8k+6
    fadd.s f14, f14, f3     # f14 = 8k+6  
    fdiv.s f16, f0, f14     # f16 = 1/(8k+6)
    fsub.s f15, f15, f16    # Final bracket term
    
    # Multiply by (1/16^k)
    fmul.s f15, f15, f11    # Multiply by 16^(-k)
    
    # Add to sum
    fadd.s f10, f10, f15
    
    # Update 16^(-k) for next iteration
    fdiv.s f11, f11, f1     # f11 = f11/16
    
    addi t2, t2, 1          # k++
    j bbp_loop
    
bbp_finish:
    # Store result
    fsw f10, pi_result, t0
    
    # Exit
    li a7, 10
    ecall
