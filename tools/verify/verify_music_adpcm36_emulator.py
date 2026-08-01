#!/usr/bin/env python3
"""Verify generated ADPCM36 as a melodic M patch zone."""

from __future__ import annotations

import re
import shutil
import struct
import subprocess
import sys
import wave as wave_module
from pathlib import Path


STATE_BASE = 0x5960


def word(data: bytes, index: int) -> int:
    return struct.unpack_from("<H", data, index * 2)[0]


def u32(data: bytes, index: int) -> int:
    return word(data, index) | (word(data, index + 1) << 16)


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    starter = root
    build = root / "build" / "music_adpcm_check"
    generated = build / "generated_audio"
    name = "MusicAdpcmCheck"
    emulator = root / "build" / "emulator-macos" / "mobigo2_emu"

    if not emulator.exists():
        subprocess.run(
            [str(root / "tools" / "build" / "emulator_macos.sh")], check=True
        )
    if build.exists():
        shutil.rmtree(build)
    generated.mkdir(parents=True)

    source_wav = generated / "clean_music.wav"
    samples = [12288] * 16 + [-12288] * 16
    with wave_module.open(str(source_wav), "wb") as destination:
        destination.setnchannels(1)
        destination.setsampwidth(2)
        destination.setframerate(1000)
        destination.writeframes(b"".join(struct.pack("<h", sample) for sample in samples))
    subprocess.run(
        [
            sys.executable,
            str(root / "tools" / "assets" / "build_adpcm36_audio.py"),
            str(source_wav),
            str(generated),
            "--prefix", "clean_music",
            "--predictor-zero",
            "--hold-envelope", "255",
        ],
        check=True,
    )
    generated_source = generated / "clean_music_adpcm36.c"

    subprocess.run(
        [
            sys.executable,
            str(root / "tools" / "build" / "build_sdk_app.py"),
            str(root / "examples" / "audio_music_adpcm36_probe.c"),
            "--extra-source", str(generated_source),
            "--output-dir", str(build),
            "--name", name,
            "--slot", "SY",
            "--without-system-ui",
            "--install-nand",
        ],
        check=True,
    )

    ram = build / "music_adpcm_ram.bin"
    log = build / "music_adpcm_emu.log"
    subprocess.run(
        [
            str(emulator),
            "--rom", str(starter / "vendor" / "firmware" / "internalrom.bin"),
            "--spi", str(starter / "vendor" / "firmware" / "spi.bin"),
            "--nand", str(build / f"nand.{name}.bin"),
            "--no-window",
            "--steps", "250000000",
            "--dump-memory", str(ram),
            "--dump-memory-base", hex(STATE_BASE),
            "--dump-memory-words", "0x30",
            "--log",
            "--log-file", str(log),
            "--start-logging-at", "200000000",
        ],
        check=True,
    )

    data = ram.read_bytes()
    status = word(data, 0)
    handle = u32(data, 1)
    wave_address = u32(data, 3)
    initial_state = word(data, 5)
    final_state = word(data, 6)
    frames = word(data, 7)
    stop_frame = word(data, 8)
    patch_words = word(data, 9)
    format_set = word(data, 10)
    phase = word(data, 20)

    if status != 0x7792:
        raise SystemExit(f"FAIL music ADPCM36 status={status:#06x}")
    if (handle & 0xF000FFFF) != 0x40000004:
        raise SystemExit(f"FAIL music ADPCM36 handle={handle:#010x}")
    if initial_state != 2 or final_state != 0:
        raise SystemExit(
            f"FAIL music ADPCM36 states={initial_state}->{final_state}"
        )
    if stop_frame < 4 or stop_frame > 24 or frames <= stop_frame or phase != 3:
        raise SystemExit(
            f"FAIL music ADPCM36 timing stop={stop_frame} frames={frames} phase={phase}"
        )
    if patch_words != 60 or format_set != 1:
        raise SystemExit(
            f"FAIL music ADPCM36 patch={patch_words} format_set={format_set}"
        )

    start_line = None
    for line in log.read_text(errors="replace").splitlines():
        if "SPU start channel=" not in line:
            continue
        match = re.search(r"wave=0x([0-9a-fA-F]+)", line)
        if match and int(match.group(1), 16) == wave_address:
            start_line = line
            break
    if start_line is None:
        raise SystemExit(
            f"FAIL music ADPCM36 no SPU start matched wave={wave_address:#x}"
        )
    fields = {
        key: int(value, 16)
        for key, value in re.findall(
            r"(wave|mode|pitch|panvol|env|format)=0x([0-9a-fA-F]+)",
            start_line,
        )
    }
    mode = fields.get("mode", -1)
    format_register = fields.get("format", -1)
    pitch = fields.get("pitch", -1)
    panvol = fields.get("panvol", -1)
    if (mode & 0xF000) != 0xF000 or format_register != 0xBE00:
        raise SystemExit(
            f"FAIL music ADPCM36 mode={mode:#06x} format={format_register:#06x}"
        )
    if pitch != 0x0747 or panvol != 0x4064:
        raise SystemExit(
            f"FAIL music ADPCM36 pitch={pitch:#x} panvol={panvol:#06x}"
        )

    print(
        "PASS resident ADPCM36 music "
        f"handle={handle:#010x} wave={wave_address:#08x} "
        f"mode={mode:#06x} format=0xbe00 pitch=0x0747 panvol=0x4064 "
        f"states=2->0 stop_frame={stop_frame}"
    )
    print("PASS automatic SPU beat IRQ4 scheduling")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
