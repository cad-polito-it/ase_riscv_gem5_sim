#!/usr/bin/env bash
# Build and simulate programs/<name> on gem5 (in-order RISC-V CPU) inside Docker.
# Results (stats.txt, .elf, .dump) are written to results/<name>/.
#
#   ./sim.sh example
#   ./sim.sh example -- --l1d_size 8kB        extra gem5 options after --
#   L1D=8kB L1I=8kB CACHELINE=32 ./sim.sh example
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/docker/lib.sh"
[[ $# -ge 1 ]] || die "usage: ./sim.sh <program-name> [-- gem5 options]   (see the programs/ folder)"
ensure_image
exec docker run --rm ${USER_ARGS[@]+"${USER_ARGS[@]}"} -v "$MOUNT":/work \
    -e L1D -e L1I -e CACHELINE "$IMAGE" ase-sim "$@"
