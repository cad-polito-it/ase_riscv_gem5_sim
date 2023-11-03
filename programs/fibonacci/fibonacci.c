#ifdef _GEM5_
#include <gem5/m5ops.h>
#endif /*_GEM5_*/


int main() {

#if _GEM5_
m5_work_begin(1,1);   
#endif /*_GEM5_*/

   volatile int n = 5, first = 0, second = 1, next;

    for (int i = 0; i < n; i++) {
        if (i <= 1)
            next = i;
        else {
            next = first + second;
            first = second;
            second = next;
        }
    }
#ifdef _GEM5_
    m5_work_end(1,1);
#endif /*_GEM5_*/

    return 0;
}
