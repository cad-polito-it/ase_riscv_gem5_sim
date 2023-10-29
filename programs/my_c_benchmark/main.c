#ifdef _GEM5_
#include <gem5/m5ops.h>
#endif /*_GEM5_*/

int main() {


/********************************************************
 *****      Starting Region of Interest (ROI)    ********
********************************************************/
#if _GEM5_
 m5_work_begin(1,1);   
#endif /*_GEM5_*/

    // my c benchmark core 

/********************************************************
 *****      End Region of Interest (ROI)         ********
********************************************************/
#ifdef _GEM5_
    m5_work_end(1,1);
#endif /*_GEM5_*/
    return 0;
}





























