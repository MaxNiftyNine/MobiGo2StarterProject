#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
if [[ "${MOBIGO_NO_LAUNCH:-0}" == "1" ]]; then
    exec python3 "$ROOT/tools/mobigo.py" build
fi
exec python3 "$ROOT/tools/mobigo.py" run "$@"
