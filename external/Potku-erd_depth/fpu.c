#ifdef FPU
#ifndef __APPLE__
/* On OSX there is no fpu_control.h. Also OSX does fp math using SSE anyway. */
#include <fpu_control.h>

/* 
 *  For intel-compatible fpu-processors default mode is 0x137f which 
 *  means that all the interrupts are masked. With value 0x1372 invalid 
 *  operation, zero division, overflow and underflow are not masked and 
 *  the program crashes when any of these occurs. This is of course a 
 *  Good Thing.
 */
 
#define FPU_MODE 0x1372
#define FPU_MASK 0x137f

void fpu(void);
void fpu_mask(void);

void fpu(void)
{
   fpu_control_t fpu_cw = FPU_MODE;

   _FPU_SETCW(fpu_cw);
     
}

void fpu_mask(void)
{
   fpu_control_t fpu_cw = FPU_MASK;

   _FPU_SETCW(fpu_cw);
     
}
#endif
#endif
