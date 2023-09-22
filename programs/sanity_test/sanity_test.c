#include <stdlib.h>
#include <stdio.h>


int myfunction(){
 // START OF YOUR CODE FOR KONATA PIPELINE
  int n=50, first = 0, second = 1, next, c;

  printf("First %d terms of Fibonacci series are:\n", n);

  for (c = 0; c < n; c++)
  {
    if (c <= 1)
      next = c;
    else
    {
      next = first + second;
      first = second;
      second = next;
    }
    printf("%d\n", next);
  }
  return c;
}

int main()
{
  int iterations;
  iterations=myfunction();
  printf("Iterations %d\n", iterations);
  return 0;
}

