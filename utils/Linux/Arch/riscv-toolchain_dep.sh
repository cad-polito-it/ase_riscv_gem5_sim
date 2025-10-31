#!/bin/bash

if [[ -d "${ROOT_DIR}/riscv-toolchain/" ]]; then 
    echo "riscv-gnu-toolchain directory already exists. Skipping. Remove it if you want to reinstall"
	exit 1
fi

##############################################################################

if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root" 
   exit 1
fi

##############################################################################

pacman -Syu --noconfirm

# Install RISC-V toolchain dependencies for Arch Linux
pacman -S --needed --noconfirm autoconf automake curl python python-pip python-tomli libmpc mpfr gmp gawk base-devel bison flex texinfo gperf libtool patchutils bc zlib expat ninja git cmake glib2 libslirp

exit 0