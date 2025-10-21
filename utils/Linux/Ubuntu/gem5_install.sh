#!/bin/bash

GEM_5_REPOSITORY="https://github.com/cad-polito-it/gem5.git"

##############################################################################

echo "Downloading gem5 tool"
git clone ${GEM_5_REPOSITORY} ${ROOT_DIR}/gem5

##############################################################################

cd ${ROOT_DIR}/gem5

##############################################################################

virtualenv -p python3.10 ${ROOT_DIR}/myenv
source ${ROOT_DIR}/myenv/bin/activate
pip3 install scons==4

##############################################################################

export PYTHON=/usr/bin/python3.10
export PYTHON_CONFIG=/usr/bin/python3.10-config

##############################################################################

scons build/RISCV/gem5.opt -j $(($(nproc) / 2))
if [[ $? -ne 0 ]]; then
	echo "Installation failed, exiting..."
	exit 1
fi

##############################################################################

cd ${WORK_DIR}

##############################################################################

exit 0