#!/usr/bin/env bash
# Run ASE Studio in Docker and open it in the browser at http://127.0.0.1:8765
#   ./studio.sh          start        ./studio.sh stop      stop
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/docker/lib.sh"
PORT="${ASE_STUDIO_PORT:-8765}"

if [[ "${1:-}" == "stop" ]]; then
    docker rm -f ase-studio >/dev/null 2>&1 && echo "ASE Studio stopped." || echo "ASE Studio was not running."
    exit 0
fi
ensure_image
[[ -f "$REPO/ase_studio/backend.py" ]] || die "ase_studio is empty. Run: git submodule update --init --recursive"

docker rm -f ase-studio >/dev/null 2>&1 || true
docker run -d --name ase-studio ${USER_ARGS[@]+"${USER_ARGS[@]}"} -p "127.0.0.1:${PORT}:8766" \
    -v "$MOUNT":/work "$IMAGE" ase-studio >/dev/null
for _ in $(seq 1 30); do
    curl -s -m 2 -o /dev/null "http://127.0.0.1:${PORT}/" && break
    sleep 1
done
URL="http://127.0.0.1:${PORT}"
echo "ASE Studio: $URL   (stop with: ./studio.sh stop)"
if command -v open >/dev/null 2>&1; then open "$URL"
elif command -v xdg-open >/dev/null 2>&1; then xdg-open "$URL" >/dev/null 2>&1 || true
elif command -v cmd.exe >/dev/null 2>&1; then cmd.exe /c start "" "$URL" >/dev/null 2>&1 || true
fi
