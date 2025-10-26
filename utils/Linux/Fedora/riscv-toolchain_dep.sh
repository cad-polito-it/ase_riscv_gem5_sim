#!/usr/bin/env bash
set -euo pipefail

if command -v dnf5 >/dev/null 2>&1; then
  PKG=dnf5
elif command -v dnf >/dev/null 2>&1; then
  PKG=dnf
else
  echo "[ERROR] dnf/dnf5 not found."
  exit 1
fi
pkg() { if [[ $EUID -eq 0 ]]; then "$PKG" "$@"; else sudo "$PKG" "$@"; fi; }


##############################################################################

if [[ -d "${ROOT_DIR}/riscv-toolchain/" ]]; then 
    echo "riscv-gnu-toolchain directory already exists. Skipping. Remove it if you want to reinstall"
	exit 0
fi

##############################################################################

if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root" 
   exit 1
fi

##############################################################################


pkg -y install gcc gcc-c++

pkg -y install \
  autoconf \
  automake \
  autoconf-archive \
  curl \
  python3 \
  python3-pip \
  python3-tomli \
  libmpc-devel \
  mpfr-devel \
  gmp-devel \
  gawk \
  bison \
  flex \
  texinfo \
  gperf \
  libtool \
  patchutils \
  bc \
  zlib-devel \
  expat-devel \
  ninja-build \
  git \
  cmake \
  glib2-devel \
  libslirp-devel
exit 0