#!/usr/bin/env bash
set -euo pipefail

# Ensure OS is set (needed by the handoff path)
# export DISTRO=$(lsb_release -ds | cut -d " " -f 1) nvm doing this. 

if ! command -v lsb_release >/dev/null 2>&1; then
  echo "lsb_release not found. Please install it and retry." >&2
  exit 1
fi

DISTRO="$(lsb_release -si 2>/dev/null)"
VER="$(lsb_release -sr 2>/dev/null)"

case "${DISTRO}" in
  Ubuntu|Fedora) ;;
  *)
    echo "${DISTRO} Not supported yet. Sorry!" >&2
    exit 1
    ;;
esac

export DISTRO VER

# Handoff
if  [ -f "${UTILS_DIR}/${OS}/${DISTRO}/${DISTRO}.sh" ]; then
  bash "${UTILS_DIR}/${OS}/${DISTRO}/${DISTRO}.sh"
fi

exit 0
