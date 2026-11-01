#!/bin/bash
# Build tools/gem5/build/RISCV/gem5.opt for macOS (Apple Silicon), the gem5
# that build_app.py puts in the app.
#  1. download gem5 (cad-polito-it/gem5, branch from ase_studio_branches.json) if missing
#  2. apply the patches in gem5_patches/ (patches already applied are skipped)
#  3. build with SCons and check the result with gem5_selftest.py
#
# Usage:  utils/macOS/build_gem5.sh [-jN]
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
GEM5="$REPO/tools/gem5"
VENV="$REPO/tools/myenv"
BREW="$(brew --prefix)"
PY="$BREW/opt/python@3.10/bin/python3.10"
JOBS="${1:--j$(sysctl -n hw.ncpu)}"

BRANCH="$("$PY" -c 'import json,sys; print(json.load(open(sys.argv[1]))["gem5"])' \
          "$REPO/ase_studio_branches.json")"

if [[ ! -d "$GEM5/.git" ]]; then
  echo "==> Downloading gem5 ($BRANCH)"
  git clone --depth 1 --branch "$BRANCH" --single-branch \
      https://github.com/cad-polito-it/gem5.git "$GEM5"
fi

echo "==> macOS patches"
for patch in "$HERE"/gem5_patches/*.patch; do
  name="$(basename "$patch")"
  if git -C "$GEM5" apply --reverse --check "$patch" 2>/dev/null; then
    echo "    $name: already applied"
  else
    git -C "$GEM5" apply "$patch"
    echo "    $name: applied"
  fi
done

if [[ ! -x "$VENV/bin/scons" ]]; then
  echo "==> SCons"
  "$PY" -m venv "$VENV"
  "$VENV/bin/pip" install --quiet "scons==4"
fi

# Some Command Line Tools versions do not search the SDK's libc++:
# in that case clang++ goes through a wrapper that adds it.
CXX=clang++
if ! echo '#include <cstddef>' | clang++ -x c++ -fsyntax-only - 2>/dev/null; then
  LIBCXX="$(xcrun --show-sdk-path)/usr/include/c++/v1"
  CXX="$REPO/tools/bin/clang++"
  mkdir -p "$(dirname "$CXX")"
  printf '#!/bin/bash\nexec /usr/bin/clang++ -isystem "%s" "$@"\n' "$LIBCXX" > "$CXX"
  chmod +x "$CXX"
  echo "==> clang++ with the libc++ of $LIBCXX"
fi

echo "==> Building gem5.opt ($JOBS)"
cd "$GEM5"
CC=clang CXX="$CXX" PYTHON="$PY" \
  PYTHON_CONFIG="$BREW/opt/python@3.10/bin/python3.10-config" \
  "$VENV/bin/scons" build/RISCV/gem5.opt "$JOBS"

echo "==> Checking"
"$PY" "$HERE/gem5_selftest.py" "$GEM5/build/RISCV/gem5.opt" \
    --toolchain "$BREW/opt/riscv64-elf-gcc/bin"
