#!/usr/bin/env bash
set -euo pipefail

##############################################################################

if [[ -f "${ROOT_DIR:-$(pwd)}/gem5_pipeline_visualizer" ]]; then
  echo "gem5_pipeline_visualizer already exists. Skipping. Remove it if you want to reinstall."
  exit 0
fi

##############################################################################

if [[ $EUID -ne 0 ]]; then
  echo "This script must be run as root"
  exit 1
fi

##############################################################################

if command -v dnf5 >/dev/null 2>&1; then
  PKG=dnf5
elif command -v dnf >/dev/null 2>&1; then
  PKG=dnf
else
  echo "[ERROR] dnf/dnf5 not found."
  exit 1
fi
pkg() { if [[ $EUID -eq 0 ]]; then "$PKG" "$@"; else sudo "$PKG" "$@"; fi; }

# pkg -y groupinstall "Development Tools"
pkg install -y git

pkg install -y \
  qt6-qtbase-devel \
  qt6-qtdeclarative-devel \
  qt6-qtwayland \
  qt6-qtwayland-devel \
  xcb-util-cursor

exit 0