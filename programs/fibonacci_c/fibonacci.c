/* Fibonacci sequence generator in C 
 * Generates the first 21 Fibonacci numbers using iterative approach
 */
int main() {
    int i;          // Loop counter
    int a = 0;          // First Fibonacci number
    int b = 1;          // Second Fibonacci number  
    int next;           // Next Fibonacci number
    int count = 21;     // Number of terms to generate
        
    // Generate and print remaining numbers
    for (i = 1; i < count; i++) {
        next = a + b;   // Calculate next Fibonacci number
        a = b;          // Update: previous second becomes first
        b = next;       // Update: calculated next becomes second
    }
    
    return 0;
}
