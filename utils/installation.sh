#!/bin/bash

ROOT_DIR=./tools

GEM_5_REPOSITORY=https://github.com/cad-polito-it/gem5.git
RISCV_TOOLCHAIN_REPOSITORY=https://github.com/riscv-collab/riscv-gnu-toolchain.git


mkdir $ROOT_DIR

cd $ROOT_DIR

if [[ -d "$ROOT_DIR/gem5" ]] ; then 
    echo "gem5 directory already exists. Remove it if you want to reinstall"
    exit 1
fi

echo "Downloading gem5 tool"
git clone $GEM_5_REPOSITORY
cd gem5
scons build/RISCV/gem5.opt -j $(nproc)

echo "Downloading RISC-V toolchain"
cd ..

if [[ -d "$ROOT_DIR/riscv-gnu-toolchain" ]] ; then 
    echo "riscv-gnu-toolchain directory already exists. Remove it if you want to reinstall"
    exit 1
fi

git clone $RISCV_TOOLCHAIN_REPOSITORY
cd riscv-gnu-toolchain
git submodule update --init --recursive
./configure --prefix=$ROOT_DIR/riscv-toolchain  --enable-multilib
make -j $(nproc)   
make install 
# clean up 
rm -rf $ROOT_DIR/riscv-gnu-toolchain
cd ..

echo "Installation completed"
echo "Update the setup_default files with the correct paths"

echo "CC: $ROOT_DIR/riscv-toolchain/bin/riscv64-unknown-elf-gcc"
echo "OBJDUMP: $ROOT_DIR/riscv-toolchain/bin/riscv64-unknown-elf-objdump"
echo "CC_INSTALLATION_PATH: $ROOT_DIR/riscv-toolchain/bin/"
echo "GEM5_INSTALLATION_PATH: $ROOT_DIR/gem5/build/"
echo "GEM5_SRC: $ROOT_DIR/gem5/"




