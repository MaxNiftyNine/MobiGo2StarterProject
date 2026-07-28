#!/bin/zsh
set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
if [[ "$EUID" -ne 0 ]]; then
    exec sudo "$0" "$@"
fi
exec python3 "$ROOT/tools/mobigo_usb/developer_mode.py" "$@"
