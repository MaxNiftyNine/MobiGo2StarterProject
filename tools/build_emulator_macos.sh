#!/bin/zsh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
command -v cmake >/dev/null || {
    echo "CMake is required to rebuild the macOS emulator."
    exit 1
}
pkg-config --exists sdl2 || {
    echo "SDL2 is required. With Homebrew: brew install sdl2 pkg-config"
    exit 1
}
cmake -S "$ROOT/emulator" -B "$ROOT/build/emulator-macos" \
    -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=OFF
cmake --build "$ROOT/build/emulator-macos" --config Release --parallel

