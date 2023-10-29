#include <stdlib.h>
#include <stdio.h>

#ifdef _GEM5_
#include <gem5/m5ops.h>
#endif /*_GEM5_*/

int myfunction(){

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

/********************************************************
*****      Starting Region of Interest (ROI)    ********
********************************************************/
#if _GEM5_
 m5_work_begin(1,1);   
#endif /*_GEM5_*/

  int iterations;
  iterations=myfunction();
  printf("Iterations %d\n", iterations);
  /********************************************************
 *****      End Region of Interest (ROI)         ********
********************************************************/
#ifdef _GEM5_
    m5_work_end(1,1);
#endif /*_GEM5_*/
  return 0;
}

