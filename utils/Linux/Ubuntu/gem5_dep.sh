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

apt update -y
apt upgrade -y

if [[ "${MAJOR}" == "20" ]]; then
	apt install -y build-essential git m4 scons zlib1g zlib1g-dev libprotobuf-dev protobuf-compiler libprotoc-dev libgoogle-perftools-dev python3-dev python-is-python3 libboost-all-dev pkg-config gcc-10 g++-10 python3-tk clang-format-18
	update-alternatives --install /usr/bin/clang-format clang-format /usr/bin/clang-format-18 180 --slave /usr/bin/clang-format-diff clang-format-diff /usr/bin/clang-format-diff-18 --slave /usr/bin/git-clang-format git-clang-format /usr/bin/git-clang-format-18
elif [[ "${MAJOR}" == "22" ]]; then
	apt install -y build-essential git m4 scons zlib1g zlib1g-dev libprotobuf-dev protobuf-compiler libprotoc-dev libgoogle-perftools-dev python3-dev libboost-all-dev pkg-config python3-tk clang-format-15
	update-alternatives --install /usr/bin/clang-format clang-format /usr/bin/clang-format-15 150  --slave /usr/bin/clang-format-diff clang-format-diff /usr/bin/clang-format-diff-15 --slave /usr/bin/git-clang-format git-clang-format /usr/bin/git-clang-format-15
elif [[ "${MAJOR}" == "24" ]]; then
	add-apt-repository ppa:deadsnakes/ppa -y
	apt update -y
	apt install build-essential scons python3-dev git pre-commit zlib1g zlib1g-dev libprotobuf-dev protobuf-compiler libprotoc-dev libgoogle-perftools-dev libboost-all-dev  libhdf5-serial-dev python3-pydot python3-venv python3-tk mypy m4 libcapstone-dev libpng-dev libelf-dev pkg-config wget cmake doxygen clang-format -y
	apt install python3.10 -y
	apt install python3.10-dev -y
fi

exit 0