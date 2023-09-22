#include <stdio.h>

int main() {
    float n = 5.0, first = 0, second = 1, next;

   // printf("Enter the number of terms: ");
   // scanf("%f", &n);

   // printf("Fibonacci Series:\n");

    for (int i = 0; i < n; i++) {
        if (i <= 1)
            next = i;
        else {
            next = first + second;
            first = second;
            second = next;
        }
        printf("%f ", next);
    }

    return 0;
}
