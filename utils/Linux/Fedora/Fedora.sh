#!/usr/bin/env bash
VER=$(rpm -E %fedora 2>/dev/null || echo "")

export MAJOR=$VER

declare -A deps
echo "HIIIII it's working"

##############################################################################

for f in ${UTILS_DIR}/${OS}/${DISTRO}/*_dep.sh; do
  fid=$(basename "${f}" | cut -d "_" -f1)
  echo "Installing dependencies for ${fid}..."
  sudo -E bash "${f}"
  if [ $? -eq 0 ]; then
    echo "Installing dependencies for ${fid} success"
    deps[${fid}]=0
  else
    echo "Installing dependencies for ${fid} failed"
    deps[${fid}]=1
  fi
done

##############################################################################

for f in ${UTILS_DIR}/${OS}/${DISTRO}/gem5-visualizer*_install.sh; do
  fid=$(basename "${f}" | cut -d "_" -f1)
  if [ "${deps[${fid}]:-1}" -eq 0 ]; then
    echo "Installing ${fid}..."
    bash "${f}"
    if [ $? -eq 0 ]; then
      echo "Installation success!"
    else
      echo "Installation failed!"
    fi
  fi
done

exit 0