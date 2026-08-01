#!/bin/zsh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
RUN_TESTS=0
BUILD_TESTING=OFF
if [[ "${1:-}" == "--test" ]]; then
    RUN_TESTS=1
    BUILD_TESTING=ON
elif [[ $# -ne 0 ]]; then
    echo "Usage: $0 [--test]" >&2
    exit 2
fi
command -v cmake >/dev/null || {
    echo "CMake is required to rebuild the macOS emulator."
    exit 1
}
PKG_CONFIG_BIN="${MOBIGO_PKG_CONFIG:-}"
if [[ -z "$PKG_CONFIG_BIN" ]]; then
    for candidate in /opt/homebrew/bin/pkg-config /usr/local/bin/pkg-config "$(command -v pkg-config 2>/dev/null || true)"; do
        if [[ -x "$candidate" ]] && "$candidate" --exists sdl2; then
            PKG_CONFIG_BIN="$candidate"
            break
        fi
    done
fi
if [[ -z "$PKG_CONFIG_BIN" ]]; then
    echo "SDL2 is required. With Homebrew: brew install sdl2 pkg-config"
    exit 1
fi
cmake -S "$ROOT/emulator" -B "$ROOT/build/emulator-macos" \
    -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING="$BUILD_TESTING" \
    -DPKG_CONFIG_EXECUTABLE="$PKG_CONFIG_BIN"
cmake --build "$ROOT/build/emulator-macos" --config Release --parallel
if [[ "$RUN_TESTS" == 1 ]]; then
    ctest --test-dir "$ROOT/build/emulator-macos" --output-on-failure
fi
