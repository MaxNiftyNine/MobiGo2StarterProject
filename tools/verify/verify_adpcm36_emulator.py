#!/usr/bin/env python3
"""Verify an original ADPCM36 W resource through resident/SPU playback."""

from __future__ import annotations

import re
import shutil
import struct
import subprocess
import sys
import wave as wave_file
from pathlib import Path


STATE_BASE = 0x59A0


def word(data: bytes, index: int) -> int:
    return struct.unpack_from("<H", data, index * 2)[0]


def u32(data: bytes, index: int) -> int:
    return word(data, index) | (word(data, index + 1) << 16)


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    starter = root
    build = root / "build" / "adpcm_check"
    name = "AdpcmCheck"
    emulator = starter / "build" / "emulator-macos" / "mobigo2_emu"

    if not emulator.exists():
        subprocess.run(
            [str(starter / "tools" / "build" / "emulator_macos.sh")],
            check=True,
        )
    if build.exists():
        shutil.rmtree(build)
    generated = build / "generated_audio"
    generated.mkdir(parents=True)
    source_wav = generated / "clean_adpcm.wav"
    samples = [12288 if index < 16 else -12288 for index in range(32)]
    with wave_file.open(str(source_wav), "wb") as destination:
        destination.setnchannels(1)
        destination.setsampwidth(2)
        destination.setframerate(1000)
        destination.writeframes(
            b"".join(struct.pack("<h", sample) for sample in samples)
        )
    subprocess.run(
        [
            sys.executable,
            str(root / "tools" / "assets" / "build_adpcm36_audio.py"),
            str(source_wav),
            str(generated),
            "--prefix", "clean_adpcm",
            "--predictor-zero",
        ],
        check=True,
    )

    subprocess.run(
        [
            sys.executable,
            str(root / "tools" / "build" / "build_sdk_app.py"),
            str(root / "examples" / "audio_adpcm36_const_boot_test.c"),
            "--output-dir", str(build),
            "--name", name,
            "--slot", "SY",
            "--without-system-ui",
            "--extra-source",
            str(generated / "clean_adpcm_adpcm36.c"),
            "--install-nand",
        ],
        check=True,
    )

    ram = build / "adpcm_ram.bin"
    log = build / "adpcm_emu.log"
    subprocess.run(
        [
            str(emulator),
            "--rom", str(starter / "vendor" / "firmware" / "internalrom.bin"),
            "--spi", str(starter / "vendor" / "firmware" / "spi.bin"),
            "--nand", str(build / f"nand.{name}.bin"),
            "--no-window",
            "--steps", "245000000",
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
    relocated = u32(data, 3)
    wave = u32(data, 5)
    initial_state = word(data, 7)
    final_state = word(data, 8)
    stop_frame = word(data, 9)
    frames = word(data, 10)
    mode = word(data, 11)
    format_register = word(data, 12)
    pitch = u32(data, 13)
    saw_positive = word(data, 15)
    saw_negative = word(data, 16)
    last_previous = word(data, 17)
    last_current = word(data, 18)

    if status != 0x7782:
        raise SystemExit(f"FAIL ADPCM36 status={status:#06x}, expected 0x7782")
    if handle != 0x40000000:
        raise SystemExit(
            f"FAIL ADPCM36 handle={handle:#010x}, expected 0x40000000"
        )
    if relocated != wave * 2:
        raise SystemExit(
            f"FAIL ADPCM36 relocation byte={relocated:#x} wave_word={wave:#x}"
        )
    if initial_state not in (0, 2) or final_state != 0:
        raise SystemExit(
            f"FAIL ADPCM36 states initial={initial_state} final={final_state}"
        )
    if stop_frame != 1 or frames <= stop_frame:
        raise SystemExit(
            f"FAIL ADPCM36 completion stop={stop_frame} frames={frames}"
        )
    if (mode & 0xC000) != 0x8000 or (mode & 0x3000) != 0x1000:
        raise SystemExit(
            f"FAIL ADPCM36 mode={mode:#06x}, expected one-shot compressed mode"
        )
    if format_register != 0xBE00:
        raise SystemExit(
            f"FAIL ADPCM36 format register={format_register:#06x}, expected 0xbe00"
        )
    if pitch != 0x0747:
        raise SystemExit(f"FAIL ADPCM36 pitch={pitch:#x}, expected 0x747")
    if saw_positive != 1 or saw_negative != 1:
        raise SystemExit(
            "FAIL ADPCM36 decoded sample levels "
            f"positive={saw_positive} negative={saw_negative} "
            f"last={last_previous:#06x}/{last_current:#06x}"
        )

    start_line = None
    for line in log.read_text(errors="replace").splitlines():
        if "SPU start channel=0" not in line:
            continue
        match = re.search(r"wave=0x([0-9a-fA-F]+)", line)
        if match and int(match.group(1), 16) == wave:
            start_line = line
            break
    if start_line is None:
        raise SystemExit(f"FAIL ADPCM36 no SPU start matched wave={wave:#x}")
    fields = {
        key: int(value, 16)
        for key, value in re.findall(
            r"(wave|mode|pitch|panvol|env)=0x([0-9a-fA-F]+)",
            start_line,
        )
    }
    if fields.get("mode") != mode or fields.get("pitch") != pitch:
        raise SystemExit(f"FAIL ADPCM36 logged setup differs: {start_line}")
    if fields.get("panvol") != 0x407F or fields.get("env") != 0x007F:
        raise SystemExit(f"FAIL ADPCM36 mixer fields: {start_line}")

    print(
        "PASS resident ADPCM36 "
        f"handle={handle:#010x} wave={wave:#08x} mode={mode:#06x} "
        f"format=0xbe00 pitch=0x0747 decoded=0xb000/0x5000 "
        f"states={initial_state}->0 stop_frame=1"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
