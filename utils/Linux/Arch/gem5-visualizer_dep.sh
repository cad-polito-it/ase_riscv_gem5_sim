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

pacman -Syu --noconfirm

# Install gem5-visualizer dependencies for Arch Linux
pacman -S --noconfirm base-devel git qt6-base qt6-declarative qt6-wayland libxcb

exit 0
