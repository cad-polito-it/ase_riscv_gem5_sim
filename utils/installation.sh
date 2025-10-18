#!/bin/bash

if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root" 
   exit 1
fi

apt update -y
apt upgrade -y

WORK_DIR=$(pwd)
ROOT_DIR="${WORK_DIR}/tools"

GEM_5_REPOSITORY="https://github.com/cad-polito-it/gem5.git"
RISCV_TOOLCHAIN_REPOSITORY="https://github.com/riscv-collab/riscv-gnu-toolchain.git"
GEM5_VISUALIZER_REPOSITORY="https://github.com/cad-polito-it/gem5_visualizer.git"

VER=$(lsb_release -a | grep Description | cut -d ":" -f2 | cut -d " " -f2)
MAJOR=$(echo $VER | cut -d "." -f1)
MINOR=$(echo $VER | cut -d "." -f2)

echo "Working with UBUNTU ${MAJOR}.${MINOR}"

if [[ ! -d "$ROOT_DIR" ]]; then 
    mkdir $ROOT_DIR
	cd $ROOT_DIR
fi 


##############################################################################

if [[ -d "${ROOT_DIR}/gem5/" ]]; then 
    echo "gem5 directory already exists. Skipping Remove it if you want to reinstall"   
else 
    echo "Downloading gem5 tool"
    git clone ${GEM_5_REPOSITORY}
	
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
		virtualenv -p python3.10 myenv
		source myenv/bin/activate
		export PYTHON=/usr/bin/python3.10
		export PYTHON_CONFIG=/usr/bin/python3.10-config
		pip3 install scons==4
	fi
	
	cd gem5
    scons build/RISCV/gem5.opt -j $(($(nproc) / 2))
	if [[ $? -ne 0 ]]; then
		echo "Installation failed, exiting..."
		exit 1
	fi
    cd ..
fi

##############################################################################

if [[ -d "${ROOT_DIR}/riscv-toolchain/" ]]; then 
    echo "riscv-gnu-toolchain directory already exists. Skipping. Remove it if you want to reinstall"
else
    echo "Installing RISC-V toolchain"
    git clone ${RISCV_TOOLCHAIN_REPOSITORY}
    cd riscv-gnu-toolchain
	apt install autoconf automake autotools-dev curl python3 python3-pip python3-tomli libmpc-dev libmpfr-dev libgmp-dev gawk build-essential bison flex texinfo gperf libtool patchutils bc zlib1g-dev libexpat-dev ninja-build git cmake libglib2.0-dev libslirp-dev -y
    ./configure --prefix=${ROOT_DIR}/riscv-toolchain  --enable-multilib
    make -j $(($(nproc) / 2))  
    make install 
	if [[ $? -ne 0 ]]; then
		echo "Installation failed, exiting..."
		rm -fr 
		exit 1
	fi
    echo "Cleaning up"
    rm -rf $ROOT_DIR/riscv-gnu-toolchain
    cd ..

fi
##############################################################################

if [[ -f "${ROOT_DIR}/gem5_pipeline_visualizer" ]]; then 
    echo "gem5_pipeline_visualizer already exists. Skipping. Remove it if you want to reinstall"
else 
    echo "Installing gem5 visualizer"
    git clone ${GEM5_VISUALIZER_REPOSITORY}
    cd gem5_visualizer
    mkdir build
    cd build
	apt install qt6-base-dev qtwayland5 qtwayland5-dev-tools libxcb-cursor0 -y
	export QT_INSTALLATION_DIR="/opt/Qt/6.8.3/gcc_64"
	if [[ ! -d "${QT_INSTALLATION_DIR}" ]]; then
		echo "Downloading QT, follow the instructions, please select custom installation, v. 6.8.3 Desktop, Include Libraries and CMAKE"
		wget https://download.qt.io/official_releases/online_installers/qt-online-installer-linux-x64-online.run
		chmod 755 qt-online-installer-linux-x64-online.run
		sudo ./qt-online-installer-linux-x64-online.run
		rm -fr qt-online-installer-linux-x64-online.run
	fi
    export PATH="${QT_INSTALLATION_DIR}/libexec:${QT_INSTALLATION_DIR}/bin:$PATH"
    export QT_FRAMEWORK_BYPASS_LICENSE_CHECK=1
    export LIBGL_ALWAYS_SOFTWARE=1
    cmake .. -DCMAKE_BUILD_TYPE=Release -DQT_CMAKE_PREFIX_PATH=${QT_INSTALLATION_DIR}
    make -j $(nproc)
	if [[ $? -ne 0 ]]; then
		echo "Installation failed, exiting..."
		exit 1
	fi
    mv gem5_pipeline_visualizer ${ROOT_DIR}/gem5_pipeline_visualizer
    cd ../..   
    echo "Cleaning up"
    rm -rf ${ROOT_DIR}/gem5_visualizer
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
