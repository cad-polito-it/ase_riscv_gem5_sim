#!/bin/bash

GEM5_VISUALIZER_REPOSITORY="https://github.com/cad-polito-it/gem5_visualizer.git"

##############################################################################

echo "Downloading gem5-visualizer"
git clone ${GEM5_VISUALIZER_REPOSITORY} ${ROOT_DIR}/gem5_visualizer

##############################################################################

cd ${ROOT_DIR}/gem5_visualizer

##############################################################################

mkdir build
cd build

FILE=""
if [[ "${ARCH}" == "x86_64" ]]; then
	FILE="qt-online-installer-linux-x64-online.run"
	export QT_INSTALLATION_DIR="/opt/Qt/6.8.3/gcc_64"	
elif [[ "${ARCH}" == "aarch64" ]]; then
	FILE="qt-online-installer-linux-arm64-online.run"
	export QT_INSTALLATION_DIR="/opt/Qt/6.8.3/gcc_arm64"
fi
if [[ ! -d "${QT_INSTALLATION_DIR}" ]]; then
	echo "Downloading QT, follow the instructions, please select custom installation, v. 6.8.3 Desktop, Include Libraries and CMAKE"
	wget "https://download.qt.io/official_releases/online_installers/${FILE}"
	chmod 755 ${FILE}
	sudo "./${FILE}"
	rm -fr ${FILE}
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

##############################################################################

cd ${WORK_DIR}

##############################################################################

exit 0
