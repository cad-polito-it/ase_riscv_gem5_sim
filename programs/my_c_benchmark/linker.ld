OUTPUT_ARCH("riscv")
ENTRY("reset_handler")

STACK_SIZE = 1k ;
MEMORY
{
    ram (airwx) : ORIGIN = 0x00000000, LENGTH = 4M
}



SECTIONS
{
    . = ORIGIN(ram);
    .text : {
        KEEP(*(.text))
    } > ram
    . = ALIGN(0x1000);

    .tohost : {
        *(.tohost)
    } > ram
    . = ALIGN(0x1000);

    .init : {
        KEEP (*(.init))
    } > ram

    .fini : {
        KEEP (*(.fini))
    } > ram

    .sbss ALIGN(4) : {
        __sbss_start = .;
        *(.sbss)
        *(.sbss.*)
        *(.gnu.linkonce.sb.*)
        __sbss_end = .;
    } > ram

    .sdata : {

        *(.srodata.cst16)
        *(.srodata.cst8)
        *(.srodata.cst4)
        *(.srodata.cst2)
        *(.srodata*)
        *(.sdata .sdata.* .gnu.linkonce.s.*)
    } > ram

    .data ALIGN(4) : {
        __data_start = .;
        *(.data)
        *(.data.*)
        *(.gnu.linkonce.d.*)
        __data_end = .;
    } > ram

    .bss ALIGN(4) : {
        _bss_start = . ;
        *(.bss .bss.* .gnu.linkonce.b.*)
        *(COMMON)
        . = ALIGN(4);
        _bss_end = . ;
    } > ram

    .tdata : {
        __tdata_begin = .;
        *(.tdata)
        __tdata_end = .;
    } > ram

    .tbss : {
        __tbss_start = .;
        *(.tbss)
        __tbss_end = .;
    } > ram

    .rodata : {
        __rodata_start = .;
        KEEP(*(.rodata))
        *(.rodata.*)
        *(.gnu.linkonce.r.*)
        __rodata_end = .;
    } > ram

    /DISCARD/ : {
        *(.eh_frame)
    }

    . = ALIGN(0x40);
    _gp = . + STACK_SIZE;

    _end = .;
}