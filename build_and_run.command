#!/bin/zsh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
audio_choice=""

for argument in "$@"; do
    case "$argument" in
        --audio) audio_choice="enabled" ;;
        --no-audio) audio_choice="disabled" ;;
        *)
            echo "Unknown option: $argument"
            echo "Usage: $0 [--audio | --no-audio]"
            exit 2
            ;;
    esac
done

echo "Building the u'nSP payload locally with Wine ..."
python3 "$ROOT/tools/build_payload_wine.py"

python3 "$ROOT/tools/assemble_nand.py" \
    --output "$ROOT/firmware/nand.us-stitched.bin"
python3 "$ROOT/tools/extract_slot_mba.py" \
    "$ROOT/firmware/nand.us-stitched.bin" \
    "$ROOT/build/SY-stock.MBA" \
    --slot SY \
    --editor "$ROOT/tools/mobigo2_nandfs_editor_v2.py"
python3 "$ROOT/tools/pack_g1_mba.py" \
    --slot SY \
    --donor "$ROOT/build/SY-stock.MBA" \
    --payload "$ROOT/build/app.bin" \
    --output "$ROOT/build/MobiGo2Starter.MBA"
python3 "$ROOT/tools/replace_g1_in_nand.py" \
    "$ROOT/firmware/nand.us-stitched.bin" \
    "$ROOT/build/MobiGo2Starter.MBA" \
    "$ROOT/build/nand.edited.bin" \
    --slot SY \
    --editor "$ROOT/tools/mobigo2_nandfs_editor_v2.py"

if [[ "${MOBIGO_NO_LAUNCH:-0}" == "1" ]]; then
    echo "PASS build, SY MBA packaging, and NAND replacement completed."
    exit 0
fi

EMU="$ROOT/emulator/macos/mobigo2_emu"
if [[ ! -x "$EMU" ]] || ! file "$EMU" | grep -q "$(uname -m)"; then
    "$ROOT/tools/build_emulator_macos.sh"
    EMU="$ROOT/build/emulator-macos/mobigo2_emu"
fi

echo "Starting Emulator2; the SY homebrew launches automatically during boot."
echo "The window opens as soon as the SY handoff completes. Press F12 to quit."
if [[ -z "$audio_choice" ]]; then
    read -r "audio_reply?Emulate host audio? This makes the emulator run slower. [y/N] "
    if [[ "${audio_reply:l}" == "y" || "${audio_reply:l}" == "yes" ]]; then
        audio_choice="enabled"
    else
        audio_choice="disabled"
    fi
fi

emu_args=(
    --rom "$ROOT/firmware/internalrom.bin"
    --spi "$ROOT/firmware/spi.bin"
    --nand "$ROOT/build/nand.edited.bin"
    --open-window-at 220000000
)
if [[ "$audio_choice" == "enabled" ]]; then
    emu_args+=(--audio)
    echo "Host audio emulation enabled."
else
    echo "Host audio emulation disabled for faster execution."
fi

exec "$EMU" "${emu_args[@]}"
