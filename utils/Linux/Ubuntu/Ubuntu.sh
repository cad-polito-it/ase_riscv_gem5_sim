#!/bin/bash

VER=$(lsb_release -a | grep Description | cut -d ":" -f2 | cut -d " " -f2)
export MAJOR=$(echo $VER | cut -d "." -f1)
export MINOR=$(echo $VER | cut -d "." -f2)
declare -A deps

##############################################################################

echo "Working with UBUNTU ${MAJOR}.${MINOR}"

##############################################################################

for f in ${UTILS_DIR}/${OS}/${DISTRO}/*_dep.sh; do
	fid=$(echo "$(basename ${f})" | cut -d "_" -f 1)
	echo "Installing dependencies for ${fid}..."
	sudo -E bash ${f}
	if [[ $? -eq 0 ]]; then
		echo "Installing dependencies for ${fid} success"
		deps[${fid}]=0
	else
		echo "Installing dependencies for ${fid} failed"
		deps[${fid}]=1
	fi
done

##############################################################################

for f in ${UTILS_DIR}/${OS}/${DISTRO}/*_install.sh; do
	fid=$(echo "$(basename ${f})" | cut -d "_" -f 1)
	if [[ ${deps[${fid}]} -eq 0 ]]; then
		echo "Installing ${fid}..."
		${f}
		if [[ $? -eq 0 ]]; then
			echo "Installation success!"
		else
			echo "Installation failed!"
		fi
	fi
done
