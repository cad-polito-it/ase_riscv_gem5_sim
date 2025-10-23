#!/bin/bash

if [[ -f "${ROOT_DIR}/gem5_pipeline_visualizer" ]]; then 
    echo "gem5_pipeline_visualizer already exists. Skipping. Remove it if you want to reinstall"
	exit 1
fi

##############################################################################

if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root" 
   exit 1
fi

##############################################################################

apt update -y
apt upgrade -y

apt install build-essential git qt6-base-dev qt6-declarative-dev qtwayland5 qtwayland5-dev-tools libxcb-cursor0 -y

if [ "${ARCH}" == "aarch64" ] && [ "${MAJOR}" == "22" ]; then
	echo "[ERROR] UBUNTU 22 is not supported on this architecture!"
	exit 1
fi

exit 0
