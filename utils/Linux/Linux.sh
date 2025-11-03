#!/usr/bin/env bash
set -euo pipefail

# Ensure OS is set (needed by the handoff path)
export DISTRO=$(lsb_release -ds | cut -d " " -f 1)

# Detect distro
if [ -r /etc/os-release ]; then
  . /etc/os-release
  case "${ID:-}" in
    ubuntu) DISTRO="Ubuntu" ;;
    fedora) DISTRO="Fedora" ;;
    *)      DISTRO="${NAME%% *}" ;;
  esac
  VER="${VERSION_ID:-}"
if command -v lsb_release >/dev/null 2>&1; then
echo "lsb_release command not found"
exit 1 
fi 
  DISTRO="$(lsb_release -si 2>/dev/null || echo Linux)"
  VER="$(lsb_release -sr 2>/dev/null || uname -r)"
else
  DISTRO="Linux"
  VER="$(uname -r)"
fi

export DISTRO VER
export MAJOR="${VER%%.*}"
export MINOR="${VER#*.}"; [ "$MINOR" = "$VER" ] && MINOR="0"

# Handoff
if  [ -f "${UTILS_DIR}/${OS}/${DISTRO}/${DISTRO}.sh" ]; then
  bash "${UTILS_DIR}/${OS}/${DISTRO}/${DISTRO}.sh"
fi

exit 0
