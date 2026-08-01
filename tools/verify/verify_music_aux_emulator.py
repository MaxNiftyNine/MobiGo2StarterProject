#!/usr/bin/env python3
"""Verify M skip and auxiliary block-transfer commands on hardware beat IRQs."""

from __future__ import annotations

import shutil
import struct
import subprocess
import sys
from pathlib import Path


STATE_BASE = 0x5960


def word(data: bytes, index: int) -> int:
    return struct.unpack_from("<H", data, index * 2)[0]


def u32(data: bytes, index: int) -> int:
    return word(data, index) | (word(data, index + 1) << 16)


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    starter = root
    build = root / "build" / "music_aux_check"
    name = "MusicAuxCheck"
    emulator = root / "build" / "emulator-macos" / "mobigo2_emu"

    if not emulator.exists():
        subprocess.run(
            [str(root / "tools" / "build" / "emulator_macos.sh")], check=True
        )
    if build.exists():
        shutil.rmtree(build)
    subprocess.run(
        [
            sys.executable,
            str(root / "tools" / "build" / "build_sdk_app.py"),
            str(root / "examples" / "audio_music_aux_probe.c"),
            "--output-dir", str(build),
            "--name", name,
            "--slot", "SY",
            "--without-system-ui",
            "--install-nand",
        ],
        check=True,
    )

    ram = build / "music_aux_ram.bin"
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
            "--dump-memory-words", "0x20",
        ],
        check=True,
    )

    data = ram.read_bytes()
    status = word(data, 0)
    handle = u32(data, 1)
    initial_state = word(data, 3)
    final_state = word(data, 4)
    frames = word(data, 5)
    stop_frame = word(data, 6)
    aux0 = word(data, 7)
    aux1 = word(data, 8)
    phase = word(data, 9)
    if status != 0x77A2:
        raise SystemExit(f"FAIL music aux status={status:#06x}")
    if (handle & 0xF000FFFF) != 0x40000004:
        raise SystemExit(f"FAIL music aux handle={handle:#010x}")
    if initial_state != 2 or final_state != 0:
        raise SystemExit(f"FAIL music aux states={initial_state}->{final_state}")
    if not (2 < stop_frame <= 24 < frames) or phase != 3:
        raise SystemExit(
            f"FAIL music aux timing stop={stop_frame} frames={frames} phase={phase}"
        )
    if (aux0, aux1) != (0x9ABC, 0xDEF0):
        raise SystemExit(
            f"FAIL music aux scratch={aux0:#06x}/{aux1:#06x}"
        )
    print(
        "PASS resident M auxiliary blocks "
        f"handle={handle:#010x} scratch=0x9abc/0xdef0 "
        f"states=2->0 stop_frame={stop_frame} automatic_irq4=1"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
