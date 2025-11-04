#!/usr/bin/env bash
set -euo pipefail

if ! command -v lsb_release >/dev/null 2>&1; then
  echo "lsb_release not found. Please install it and retry." >&2
  exit 1
fi

# Ensure OS is set (needed by the handoff path)
# export DISTRO=$(lsb_release -ds | cut -d " " -f 1) nvm doing this. 
DISTRO=$(lsb_release -is)

if  [[ -z "${DISTRO}" ]]; then
	echo "Could not determine Linux distribution."
	exit 1
elif [[ "${DISTRO}" == "Arch" || "${DISTRO}" == "ManjaroLinux" ]]; then
	DISTRO="Arch"
fi

export DISTRO

# Handoff
if  [ -f "${UTILS_DIR}/${OS}/${DISTRO}/${DISTRO}.sh" ]; then
  bash "${UTILS_DIR}/${OS}/${DISTRO}/${DISTRO}.sh"
else
  echo "Unsupported Linux distribution: ${DISTRO}"
  exit 1
fi

exit 0
