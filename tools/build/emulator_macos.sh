#!/usr/bin/env bash
# Compatibility wrapper. The actual host builder supports both macOS and Linux.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
exec bash "$ROOT/tools/build/emulator_unix.sh" "$@"
