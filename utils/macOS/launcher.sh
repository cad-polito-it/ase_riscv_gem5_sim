#!/bin/bash
# Start the ASE Studio server for the native window (Contents/MacOS/ASEStudio).
# Everything it needs (Python, gem5, RISC-V compiler, make) is inside the app;
# the user's projects live in ~/ASE Studio, created on first launch.
#  1. set up an environment that points to the tools bundled in the app
#  2. create/complete the workspace by copying the project template
#  3. run the server (prints "ASE Studio: http://127.0.0.1:PORT")

RES="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_PATH="$(cd "$RES/../.." && pwd)"
FW="$(cd "$RES/../Frameworks" && pwd)"
PY="$FW/Python.framework/Versions/3.10/bin/python3.10"
SUPPORT="$HOME/Library/Application Support/ASE Studio"
WS="${ASE_STUDIO_WORKSPACE:-$HOME/ASE Studio}"
LOG="$HOME/Library/Logs/ASE Studio.log"
mkdir -p "$(dirname "$LOG")"
exec > >(tee "$LOG") 2>&1

# ---- 1. environment: only the app's tools and the system (no Homebrew)
# The Makefiles use $(CC) unquoted: the tools must be reachable through a
# path without spaces (the app is called "ASE Studio.app").
LINK_DIR="$HOME/.ase-studio"
mkdir -p "$LINK_DIR" && ln -sfn "$RES" "$LINK_DIR/app"
TOOLS="$LINK_DIR/app"
[[ "$TOOLS" == *" "* ]] && TOOLS="$RES"
export ASE_STUDIO_TOOLS="$TOOLS"
export PATH="$TOOLS/bin:$TOOLS/toolchain/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export PYTHONHOME="$FW/Python.framework/Versions/3.10"
export PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
unset PYTHONPATH PYTHONSTARTUP
export RISCV_TOOLCHAIN_PATH="$TOOLS/toolchain/bin"
export GEM5_INSTALLATION_PATH="$TOOLS/gem5/build/"
export GEM5_SRC="$TOOLS/gem5/"

# If the app was downloaded, remove the quarantine from the bundled
# executables (gem5, cc1, ...), or Gatekeeper blocks them on first use.
if xattr -p com.apple.quarantine "$APP_PATH" >/dev/null 2>&1; then
  xattr -dr com.apple.quarantine "$APP_PATH" 2>/dev/null || true
fi

# ---- 2. workspace: copy only the missing files, never overwrite
mkdir -p "$WS" && /bin/cp -Rn "$RES/project/." "$WS/" 2>/dev/null
[[ -f "$WS/setup_default" ]] || { echo "Could not create the workspace: $WS"; exit 1; }
cd "$WS" || exit 1
export ASE_STUDIO_HOST_ROOT="$WS"
# Same reason as for the tools: the Makefiles include $(ASE_STUDIO_DEMO_MK)
# unquoted, and the workspace is called "ASE Studio".
ln -sfn "$WS" "$LINK_DIR/workspace" && export ASE_STUDIO_WORKSPACE_LINK="$LINK_DIR/workspace"

# ---- 3. updated ASE Studio (if present and working), otherwise the bundled one
export ASE_STUDIO_DIR="$RES/ase_studio"
if [[ -f "$SUPPORT/ase_studio/backend.py" ]]; then
  if ASE_STUDIO_DIR="$SUPPORT/ase_studio" "$PY" "$RES/ase_studio_app.py" --check-startup; then
    export ASE_STUDIO_DIR="$SUPPORT/ase_studio"
  else
    echo "The updated ASE Studio does not start: using the version bundled in the app."
  fi
fi

exec "$PY" "$RES/ase_studio_app.py" "${ASE_STUDIO_PORT:-8765}"
