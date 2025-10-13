#!/bin/bash

ROOT_DIR=./tools

GEM_5_REPOSITORY=https://github.com/cad-polito-it/gem5.git
RISCV_TOOLCHAIN_REPOSITORY=https://github.com/riscv-collab/riscv-gnu-toolchain.git
GEM5_VISUALIZER_REPOSITORY=https://github.com/cad-polito-it/gem5_visualizer.git


if [ -z "$QT_INSTALLATION_DIR" ]; then
    echo "QT_INSTALLATION_DIR is not set. Please set it to the Qt installation directory."
    echo "You can download Qt from https://doc.qt.io/qt-6/get-and-install-qt.html"
    echo "And install the 6.8.3 version (VERY IMPORTANT)"
    echo "Select custom installation for desktop version and needed libs"
    exit 1
fi

mkdir $ROOT_DIR

cd $ROOT_DIR

if [[ -d "$ROOT_DIR/gem5" ]] ; then 
    echo "gem5 directory already exists. Remove it if you want to reinstall"
    exit 1
fi

##############################################################################

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

##############################################################################

echo "Installing RISC-V toolchain"
git clone $RISCV_TOOLCHAIN_REPOSITORY
cd riscv-gnu-toolchain
git submodule update --init --recursive
./configure --prefix=$ROOT_DIR/riscv-toolchain  --enable-multilib
make -j $(nproc)   
make install 

echo "Cleaning up"
rm -rf $ROOT_DIR/riscv-gnu-toolchain
cd ..

##############################################################################
echo "Installing gem5 visualizer"
git clone $GEM5_VISUALIZER_REPOSITORY
cd gem5_visualizer
mkdir build
cd build
export PATH="${QT_INSTALLATION_DIR}/libexec:${QT_INSTALLATION_DIR}/bin:$PATH"
export QT_FRAMEWORK_BYPASS_LICENSE_CHECK=1
export LIBGL_ALWAYS_SOFTWARE=1
cmake .. -DCMAKE_BUILD_TYPE=Release -DQT_CMAKE_PREFIX_PATH=${QT_INSTALLATION_DIR}
make -j $(nproc)
mv gem5_pipeline_visualizer $ROOT_DIR/gem5_pipeline_visualizer
cd ../..   
echo "Cleaning up"
rm -rf $ROOT_DIR/gem5_visualizer

##############################################################################

echo "Installation completed"
echo "Updating setup_default with new paths"

sed -i "s|^export CC=.*|export CC=$ROOT_DIR/riscv-toolchain/bin/riscv64-unknown-elf-gcc|" setup_default
sed -i "s|^export OBJDUMP=.*|export OBJDUMP=$ROOT_DIR/riscv-toolchain/bin/riscv64-unknown-elf-objdump|" setup_default
sed -i "s|^export CC_INSTALLATION_PATH=.*|export CC_INSTALLATION_PATH=$ROOT_DIR/riscv-toolchain/bin/|" setup_default
sed -i "s|^export GEM5_INSTALLATION_PATH=.*|export GEM5_INSTALLATION_PATH=$ROOT_DIR/gem5/build/|" setup_default
sed -i "s|^export GEM5_SRC=.*|export GEM5_SRC=$ROOT_DIR/gem5/|" setup_default
sed -i "s|^export PIPELINE_VISUALIZER=.*|export PIPELINE_VISUALIZER=$ROOT_DIR/gem5_pipeline_visualizer|" setup_default
