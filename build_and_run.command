#!/bin/zsh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
BUILD_HOST="${MOBIGO_BUILD_HOST:-max@DESKTOP-BTTG0A6.local}"
REMOTE_NAME="${MOBIGO_REMOTE_NAME:-MobiGo2StarterBuild}"
SSH_OPTIONS=(-o ConnectTimeout=10 -o StrictHostKeyChecking=accept-new)
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

ssh_cmd() {
    if [[ -n "${MOBIGO_SSH_PASSWORD:-}" ]]; then
        command -v sshpass >/dev/null ||
            { echo "MOBIGO_SSH_PASSWORD is set but sshpass is not installed."; exit 1; }
        SSHPASS="$MOBIGO_SSH_PASSWORD" sshpass -e ssh "${SSH_OPTIONS[@]}" "$@"
    else
        ssh "${SSH_OPTIONS[@]}" "$@"
    fi
}

scp_cmd() {
    if [[ -n "${MOBIGO_SSH_PASSWORD:-}" ]]; then
        SSHPASS="$MOBIGO_SSH_PASSWORD" sshpass -e scp "${SSH_OPTIONS[@]}" "$@"
    else
        scp "${SSH_OPTIONS[@]}" "$@"
    fi
}

echo "Building the u'nSP payload on $BUILD_HOST ..."
if ! ssh_cmd "$BUILD_HOST" \
    "cmd.exe /c dir %USERPROFILE%\\MobiGo2Compiler\\unSPIDE_4.1.1\\toolchain\\udocc.exe ^>nul 2^>nul"; then
    echo "Uploading the bundled Generalplus compiler (one-time remote cache) ..."
    mkdir -p "$ROOT/build"
    rm -f "$ROOT/build/MobiGo2Compiler.zip"
    (
        cd "$ROOT/compiler/windows"
        zip -qr "$ROOT/build/MobiGo2Compiler.zip" unSPIDE_4.1.1 \
            -x '*/._*' -x '*/.DS_Store'
    )
    scp_cmd "$ROOT/build/MobiGo2Compiler.zip" \
        "$BUILD_HOST:MobiGo2Compiler.zip"
    ssh_cmd "$BUILD_HOST" \
        'powershell.exe -NoProfile -Command "Remove-Item -Recurse -Force $env:USERPROFILE\MobiGo2Compiler -ErrorAction SilentlyContinue; Expand-Archive -Force $env:USERPROFILE\MobiGo2Compiler.zip $env:USERPROFILE\MobiGo2Compiler"'
fi
ssh_cmd "$BUILD_HOST" "cmd.exe /c if exist %USERPROFILE%\\$REMOTE_NAME rmdir /s /q %USERPROFILE%\\$REMOTE_NAME"
ssh_cmd "$BUILD_HOST" "cmd.exe /c mkdir %USERPROFILE%\\$REMOTE_NAME\\tools"
scp_cmd -r "$ROOT/src" "$ROOT/project" "$BUILD_HOST:$REMOTE_NAME/"
scp_cmd "$ROOT/tools/build_payload.ps1" "$ROOT/tools/srec_to_bin.py" \
    "$BUILD_HOST:$REMOTE_NAME/tools/"
ssh_cmd "$BUILD_HOST" \
    "cmd.exe /c \"set UNSP_IDE=%USERPROFILE%\\MobiGo2Compiler\\unSPIDE_4.1.1&& powershell.exe -NoProfile -ExecutionPolicy Bypass -File %USERPROFILE%\\$REMOTE_NAME\\tools\\build_payload.ps1\""
mkdir -p "$ROOT/build"
scp_cmd "$BUILD_HOST:$REMOTE_NAME/build/app.bin" "$ROOT/build/app.bin"

python3 "$ROOT/tools/pack_g1_mba.py" \
    --donor "$ROOT/firmware/G1-stock.MBA" \
    --payload "$ROOT/build/app.bin" \
    --output "$ROOT/build/MobiGo2Starter.MBA"
python3 "$ROOT/tools/assemble_nand.py" \
    --output "$ROOT/firmware/nand.us-stitched.bin"
python3 "$ROOT/tools/replace_g1_in_nand.py" \
    "$ROOT/firmware/nand.us-stitched.bin" \
    "$ROOT/build/MobiGo2Starter.MBA" \
    "$ROOT/build/nand.edited.bin" \
    --editor "$ROOT/tools/mobigo2_nandfs_editor_v2.py"

if [[ "${MOBIGO_NO_LAUNCH:-0}" == "1" ]]; then
    echo "PASS build, MBA packaging, and NAND replacement completed."
    exit 0
fi

EMU="$ROOT/emulator/macos/mobigo2_emu"
if [[ ! -x "$EMU" ]] || ! file "$EMU" | grep -q "$(uname -m)"; then
    "$ROOT/tools/build_emulator_macos.sh"
    EMU="$ROOT/build/emulator-macos/mobigo2_emu"
fi

echo "Starting Emulator2; Hamster Highway and Easy will be selected automatically."
echo "The window opens after both scripted menu presses. Press F12 to quit."
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
    --touch-event 350000000,5000000,165,82
    --touch-event 680000000,5000000,100,205
    --open-window-at 760000000
)
if [[ "$audio_choice" == "enabled" ]]; then
    emu_args+=(--audio)
    echo "Host audio emulation enabled."
else
    echo "Host audio emulation disabled for faster execution."
fi

exec "$EMU" "${emu_args[@]}"
