#!/bin/bash

export DISTRO=$(lsb_release -is)

if  [[ -z "${DISTRO}" ]]; then
	echo "Could not determine Linux distribution."
	exit 1
elif [[ "${DISTRO}" == "Arch" || "${DISTRO}" == "ManjaroLinux" ]]; then
	export DISTRO="Arch"
else
	echo "Unsupported Linux distribution: ${DISTRO}"
	exit 1
fi

##############################################################################

if [ -f "${UTILS_DIR}/${OS}/${DISTRO}/${DISTRO}.sh" ]; then
	${UTILS_DIR}/${OS}/${DISTRO}/${DISTRO}.sh
fi

exit 0
