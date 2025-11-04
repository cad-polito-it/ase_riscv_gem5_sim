#!/usr/bin/env bash
set -euo pipefail

RISCV_TOOLCHAIN_REPOSITORY="https://github.com/riscv-collab/riscv-gnu-toolchain.git"
PREFIX_DIR="${ROOT_DIR}/riscv-toolchain"

if [[ -d "${PREFIX_DIR}" ]]; then
  echo "riscv-toolchain already installed at ${PREFIX_DIR} — skipping."
  exit 0
fi

##############################################################################

echo "Installing RISC-V toolchain"
git clone ${RISCV_TOOLCHAIN_REPOSITORY} ${ROOT_DIR}/riscv-gnu-toolchain
git submodule update --init --recursive
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