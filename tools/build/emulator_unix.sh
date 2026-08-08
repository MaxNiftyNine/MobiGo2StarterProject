#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
RUN_TESTS=0
BUILD_TESTING=OFF
if [[ "${1:-}" == "--test" ]]; then
    RUN_TESTS=1
    BUILD_TESTING=ON
elif [[ $# -ne 0 ]]; then
    echo "Usage: bash $0 [--test]" >&2
    exit 2
fi

command -v cmake >/dev/null 2>&1 || {
    echo "CMake is required to build Emulator2." >&2
    exit 1
}

PKG_CONFIG_BIN="${MOBIGO_PKG_CONFIG:-}"
if [[ -z "$PKG_CONFIG_BIN" ]]; then
    candidates=(/opt/homebrew/bin/pkg-config /usr/local/bin/pkg-config)
    if command -v pkg-config >/dev/null 2>&1; then
        candidates+=("$(command -v pkg-config)")
    fi
    for candidate in "${candidates[@]}"; do
        if [[ -x "$candidate" ]] && "$candidate" --exists sdl2; then
            PKG_CONFIG_BIN="$candidate"
            break
        fi
    done
fi
if [[ -z "$PKG_CONFIG_BIN" ]]; then
    echo "SDL2 and pkg-config are required to build Emulator2." >&2
    echo "macOS: brew install cmake pkg-config sdl2" >&2
    echo "Debian/Ubuntu: sudo apt install cmake g++ pkg-config libsdl2-dev" >&2
    exit 1
fi

BUILD_DIR="$ROOT/build/emulator-host"
cmake -S "$ROOT/emulator" -B "$BUILD_DIR" \
    -DCMAKE_BUILD_TYPE=Release \
    -DBUILD_TESTING="$BUILD_TESTING" \
    -DPKG_CONFIG_EXECUTABLE="$PKG_CONFIG_BIN"
cmake --build "$BUILD_DIR" --config Release --parallel
if [[ "$RUN_TESTS" == 1 ]]; then
    ctest --test-dir "$BUILD_DIR" --output-on-failure
fi
