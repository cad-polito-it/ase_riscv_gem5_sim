#!/bin/bash

##############################################################################

export OS=$(uname -s)
export ARCH=$(uname -m)
export WORK_DIR=$(pwd)
export ROOT_DIR="${WORK_DIR}/tools"
export UTILS_DIR="${WORK_DIR}/utils"

##############################################################################

if [[ ! -d "$ROOT_DIR" ]]; then 
    mkdir $ROOT_DIR
	cd $ROOT_DIR
fi 

if [ -f "${UTILS_DIR}/${OS}/${OS}.sh" ]; then
	${UTILS_DIR}/${OS}/${OS}.sh
fi

##############################################################################

echo "Installation completed"
echo "Updating setup_default with new paths"

cd ${WORK_DIR}
sed -i "s|^export CC=.*|export CC=$ROOT_DIR/riscv-toolchain/bin/riscv64-unknown-elf-gcc|" setup_default
sed -i "s|^export OBJDUMP=.*|export OBJDUMP=$ROOT_DIR/riscv-toolchain/bin/riscv64-unknown-elf-objdump|" setup_default
sed -i "s|^export CC_INSTALLATION_PATH=.*|export CC_INSTALLATION_PATH=$ROOT_DIR/riscv-toolchain/bin/|" setup_default
sed -i "s|^export GEM5_INSTALLATION_PATH=.*|export GEM5_INSTALLATION_PATH=$ROOT_DIR/gem5/build/|" setup_default
sed -i "s|^export GEM5_SRC=.*|export GEM5_SRC=$ROOT_DIR/gem5/|" setup_default
sed -i "s|^export PIPELINE_VISUALIZER=.*|export PIPELINE_VISUALIZER=$ROOT_DIR/gem5_pipeline_visualizer|" setup_default