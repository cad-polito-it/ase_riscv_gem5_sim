# Data section
.section .data
# Place here your program data. In this example
# two vector of floats, a vector of ints anda single int are defined
T0: .word 0x0BADC0DE

# Code section
.section .text
# The _start label signals the entry point of your program
# DO NOT CHANGE ITS NAME. It must be “_start”, not “start”,
# not “main”, not “start_”. 
# It’s “_start” with a leading underscore and
# all lowercase letters
.globl _start 
_start:
# In the _start area, load the first byte/word of each of 
# the areas declared in the .data section
# This is needed to load data in the cache and avoid 
# pipeline stalls later


Main:
    # Initialize Fibonacci variables
    li x1, 0        # x1 = a = first Fibonacci number (0)
    li x2, 1        # x2 = b = second Fibonacci number (1) 
    li x3, 21       # x3 = count = number of terms to generate
    li x4, 0        # x4 = i = loop counter
    
    # Loop to generate and print remaining 20 numbers
    addi x4, x4, 1  # i = 1 (start from second iteration)
    
fib_loop:
    beq x4, x3, End # if i == count, exit loop
        
    # Calculate next Fibonacci number
    add x5, x1, x2  # x5 = next = a + b
    
    # Update variables for next iteration
    mv x1, x2       # a = b (previous second becomes first)
    mv x2, x5       # b = next (calculated next becomes second)
    # Increment counter and continue loop
    addi x4, x4, 1  # i++
    j fib_loop      # Jump back to loop start
        
End:
# exit() syscall. This is needed to end the simulation
# gracefully
    li a0, 0
    li a7, 93
    ecall
