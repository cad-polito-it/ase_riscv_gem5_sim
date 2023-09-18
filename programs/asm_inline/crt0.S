
/* ========================================================= [ entry ] === */
  .section .text,"ax",@progbits
  .global reset_handler
reset_handler:

  /* set 0 in mtvec (base for IVT) */
  //csrrw x0, mtvec, x0

  /* set all registers to zero */
  mv  x1, x0
  mv  x2, x1
  mv  x3, x1
  mv  x4, x1
  mv  x5, x1
  mv  x6, x1
  mv  x7, x1
  mv  x8, x1
  mv  x9, x1
  mv x10, x1
  mv x11, x1
  mv x12, x1
  mv x13, x1
  mv x14, x1
  mv x15, x1
  mv x16, x1
  mv x17, x1
  mv x18, x1
  mv x19, x1
  mv x20, x1
  mv x21, x1
  mv x22, x1
  mv x23, x1
  mv x24, x1
  mv x25, x1
  mv x26, x1
  mv x27, x1
  mv x28, x1
  mv x29, x1
  mv x30, x1
  mv x31, x1

  /* stack initilization */
  la   sp, _gp

_start:
  .global _start


main_entry:
  /* jump to main program entry point (argc = argv = 0) */
  jal x1, main

/*it should never reach this part*/
  j m5_exit
  
  __main_exit_handler__:
  j __main_exit_handler__ 


  .global _init
  .global _fini
_init:
_fini:
  # These don't have to do anything since we use init_array/fini_array.
  ret

/* =================================================== [ exceptions ] === */
/* This section has to be down here, since we have to disable rvc for it  */

  .section .vectors, "ax"
  .option norvc;

  // external interrupts are handled by the same callback
  // until compiler supports IRQ routines
  .org 0x00
  .rept 23
  nop                       // unused
  .endr
  __unhandled_exception__:
    j __unhandled_exception__
  

  // reset vector
  .org 0x80
  jal x0, reset_handler

  