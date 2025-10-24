#!/usr/bin/env bash

set -euo pipefail

GEM5_VISUALIZER_REPOSITORY="https://github.com/cad-polito-it/gem5_visualizer.git"
SRC_DIR="${ROOT_DIR}/gem5_visualizer"
BUILD_DIR="${SRC_DIR}/build"
APP_NAME="gem5_pipeline_visualizer"
QT_DIR=${QT_INSTALLATION_DIR} # <-- your Qt install
##############################################################################

if [[ -f "${ROOT_DIR}/${APP_NAME}" ]]; then
  echo "${APP_NAME} already exists. Skipping. Remove it if you want to reinstall."
  exit 0
fi

##############################################################################

if [[ ! -d "${QT_DIR}" || ! -d "${QT_DIR}/bin" || ! -d "${QT_DIR}/libexec" ]]; then
  echo "[ERROR] QT_DIR does not look valid: ${QT_DIR}"
  echo "        Expected subdirs: bin/ and libexec/"
  exit 1
fi

##############################################################################

CMAKE="/usr/bin/cmake"
if ! command -v "${CMAKE}" >/dev/null 2>&1; then
  echo "[ERROR] CMake not found at ${CMAKE}"
  exit 1
fi

##############################################################################

CMAKE_VER="$(${CMAKE} --version | awk 'NR==1{print $3}')"
CMAKE_MAJOR="${CMAKE_VER%%.*}"
CMAKE_MINOR="$(echo "${CMAKE_VER}" | cut -d. -f2)"
if ! { [ "${CMAKE_MAJOR}" -eq 3 ] && [ "${CMAKE_MINOR}" -ge 28 ]; } && ! { [ "${CMAKE_MAJOR}" -lt 4 ] && [ "${CMAKE_MAJOR}" -gt 3 ]; }; then
  echo "[ERROR] CMake ${CMAKE_VER} does not satisfy >=3.28 and <4.x"
  exit 1
fi

##############################################################################

echo "Downloading gem5-visualizer"
if [[ -d "${SRC_DIR}/.git" ]]; then
  echo "Repo already present at ${SRC_DIR} (skipping clone)"
else
  git clone "${GEM5_VISUALIZER_REPOSITORY}" "${SRC_DIR}"
fi

##############################################################################

mkdir -p "${BUILD_DIR}"
cd "${BUILD_DIR}"

##############################################################################

export PATH="${QT_DIR}/libexec:${QT_DIR}/bin:${PATH}"
export QT_FRAMEWORK_BYPASS_LICENSE_CHECK=1
export LIBGL_ALWAYS_SOFTWARE=1

##############################################################################

"${CMAKE}" .. -DCMAKE_BUILD_TYPE=Release -DQT_CMAKE_PREFIX_PATH="${QT_DIR}"
make

##############################################################################

mv "./${APP_NAME}" "${ROOT_DIR}/${APP_NAME}"



cd "${SRC_DIR}"
rm -rf "${BUILD_DIR}"
echo "Removed build directory: ${BUILD_DIR}"

cd "${WORK_DIR}"
echo "${APP_NAME} installed at ${ROOT_DIR}/${APP_NAME}"

exit 0
