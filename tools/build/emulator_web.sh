#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="$ROOT/emulator/web/dist"
BUILD="$ROOT/build/web"

if ! command -v emcmake >/dev/null 2>&1; then
  echo "Emscripten is required. Install/activate emsdk, then run this script again." >&2
  exit 1
fi

rm -rf "$BUILD" "$OUT"
mkdir -p "$OUT"
emcmake cmake -S "$ROOT/emulator" -B "$BUILD" -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=OFF
cmake --build "$BUILD" --target mobigo2_emu --parallel

cp "$ROOT/emulator/web/index.html" "$ROOT/emulator/web/style.css" "$ROOT/emulator/web/.nojekyll" "$OUT/"
cp "$BUILD/mobigo2_emu.js" "$BUILD/mobigo2_emu.wasm" "$BUILD/mobigo2_emu.data" "$OUT/"

EMSDK_ROOT="${EMSDK:-}"
PACKAGER="$(find "$EMSDK_ROOT" "$EMSDK_ROOT/upstream/emscripten" "$EMSDK_ROOT/tools" -name file_packager.py -print -quit 2>/dev/null || true)"
if [ -z "$PACKAGER" ]; then
  PACKAGER="$(dirname "$(command -v emcc)")/tools/file_packager.py"
fi
python3 "$PACKAGER" "$OUT/nand_part01.data" --preload "$ROOT/vendor/firmware/nand.us-stitched.bin.part01@/nand.bin.part01" --js-output="$OUT/nand_part01.js"

echo "Web build written to $OUT"
