#!/bin/bash

if [[ -d "${ROOT_DIR}/gem5/" ]]; then 
    echo "gem5 directory already exists. Skipping Remove it if you want to reinstall"
	exit 1
fi

##############################################################################

if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root" 
   exit 1
fi

##############################################################################

pacman -Syu --noconfirm

# Install gem5 dependencies for Arch Linux
pacman -S --needed --noconfirm base-devel git m4 scons zlib protobuf gperftools python boost pkg-config tk python-virtualenv hdf5 python-pydot mypy capstone libpng libelf wget cmake doxygen
# Install Python 3.10 from source
su $(logname) -c "git clone https://aur.archlinux.org/python310.git"
cd python310
su $(logname) -c "makepkg -si"

exit 0
