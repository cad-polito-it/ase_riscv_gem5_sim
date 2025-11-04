#!/usr/bin/env bash
set -euo pipefail


if [[ $EUID -ne 0 ]]; then
  echo "Run as root (e.g.,: sudo $0)"
  exit 1
fi
##############################################################################
# Pick package manager
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


# Build deps for gem5
pkg install -y \
  gcc gcc-c++ make git m4 scons zlib-devel protobuf-devel protobuf-compiler \
  gperftools-devel python3-devel boost-devel pkgconfig clang-format \
  python3-virtualenv cmake python3-pip libstdc++-devel

exit 0
