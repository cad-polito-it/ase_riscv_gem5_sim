#!/bin/bash

RISCV_TOOLCHAIN_REPOSITORY="https://github.com/riscv-collab/riscv-gnu-toolchain.git"

##############################################################################

echo "Installing RISC-V toolchain"
git clone ${RISCV_TOOLCHAIN_REPOSITORY} ${ROOT_DIR}/riscv-gnu-toolchain

##############################################################################

cd ${ROOT_DIR}/riscv-gnu-toolchain

##############################################################################

./configure --prefix=${ROOT_DIR}/riscv-toolchain --enable-multilib
make -j $(($(nproc) / 2))  
make install 
if [[ $? -ne 0 ]]; then
	echo "Installation failed, exiting..."
	rm -fr 
	exit 1
fi
echo "Cleaning up"
rm -rf ${ROOT_DIR}/riscv-gnu-toolchain

##############################################################################

cd ${WORK_DIR}

##############################################################################

exit 0