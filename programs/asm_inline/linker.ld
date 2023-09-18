OUTPUT_ARCH("riscv")
ENTRY("reset_handler")

STACK_SIZE = 2k ;
MEMORY
{
    testram (airwx) : ORIGIN = 0x80000000, LENGTH = 4M
}



SECTIONS
{
    . = ORIGIN(testram);
    .text : {
        KEEP(*(.text))
    } > testram
    . = ALIGN(0x1000);

    .tohost : {
        *(.tohost)
    } > testram
    . = ALIGN(0x1000);

    .init : {
        KEEP (*(.init))
    } > testram

    .fini : {
        KEEP (*(.fini))
    } > testram

    .sbss ALIGN(4) : {
        __sbss_start = .;
        *(.sbss)
        *(.sbss.*)
        *(.gnu.linkonce.sb.*)
        __sbss_end = .;
    } > testram

    .sdata : {
        _gp = . + STACK_SIZE;
        *(.srodata.cst16)
        *(.srodata.cst8)
        *(.srodata.cst4)
        *(.srodata.cst2)
        *(.srodata*)
        *(.sdata .sdata.* .gnu.linkonce.s.*)
    } > testram

    .data ALIGN(4) : {
        __data_start = .;
        *(.data)
        *(.data.*)
        *(.gnu.linkonce.d.*)
        __data_end = .;
    } > testram

    .bss ALIGN(4) : {
        _bss_start = . ;
        *(.bss .bss.* .gnu.linkonce.b.*)
        *(COMMON)
        . = ALIGN(4);
        _bss_end = . ;
    } > testram

    .tdata : {
        __tdata_begin = .;
        *(.tdata)
        __tdata_end = .;
    } > testram

    .tbss : {
        __tbss_start = .;
        *(.tbss)
        __tbss_end = .;
    } > testram

    .rodata : {
        __rodata_start = .;
        KEEP(*(.rodata))
        *(.rodata.*)
        *(.gnu.linkonce.r.*)
        __rodata_end = .;
    } > testram

    /DISCARD/ : {
        *(.eh_frame)
    }

    _end = .;
}