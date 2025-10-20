#!/bin/bash

export DISTRO=$(lsb_release -ds | cut -d " " -f 1)

##############################################################################

if [ -f "${UTILS_DIR}/${OS}/${DISTRO}/${DISTRO}.sh" ]; then
	${UTILS_DIR}/${OS}/${DISTRO}/${DISTRO}.sh
fi

exit 0
