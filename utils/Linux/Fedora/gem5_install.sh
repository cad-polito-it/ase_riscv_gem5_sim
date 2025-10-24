#!/usr/bin/env bash

set -euo pipefail

GEM_5_REPOSITORY="https://github.com/cad-polito-it/gem5.git"

##############################################################################

if [[ -f "${ROOT_DIR}/gem5" ]]; then 
    echo "gem5 already exists. Skipping. Remove it if you want to reinstall"
	exit 0
else
    echo "Downloading gem5 tool"
    git clone ${GEM_5_REPOSITORY} ${ROOT_DIR}/gem5
fi
##############################################################################

cd ${ROOT_DIR}/gem5
python3.10 -m venv ${ROOT_DIR}/myenv
source ${ROOT_DIR}/myenv/bin/activate

export PYTHON=/usr/bin/python3.10
export PYTHON_CONFIG=/usr/bin/python3.10-config

pip install scons==4

##############################################################################
scons build/RISCV/gem5.opt -j $(($(nproc) / 2))
if [[ $? -ne 0 ]]; then
	echo "Installation failed, exiting..."
	exit 1
fi

cd "${WORK_DIR}"
exit 0
