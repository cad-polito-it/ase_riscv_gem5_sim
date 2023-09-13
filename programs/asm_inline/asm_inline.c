#include <stdio.h>

int main() {
    int x = 5;
    int y = 10;
    int result;

    // Inline RISC-V assembly
    asm volatile (
        "add %0, %1, %2\n\t"
        : "=r" (result) // Output operand
        : "r" (x), "r" (y) // Input operands
    );

    printf("Result: %d\n", result);

    return 0;
}





























