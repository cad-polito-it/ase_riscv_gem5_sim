#!/usr/bin/env bash
set -euo pipefail
root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export ASE_STUDIO_HOST_ROOT="$root_dir"
exec "$root_dir/ase_studio/launch.sh"
