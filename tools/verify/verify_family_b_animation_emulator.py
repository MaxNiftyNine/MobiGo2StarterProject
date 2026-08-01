#!/usr/bin/env python3
"""Verify authored family-B record advancement and position deltas."""

from __future__ import annotations

import shutil
import struct
import subprocess
import sys
from pathlib import Path


BASE = 0x58B0


def word(data: bytes, index: int) -> int:
    return struct.unpack_from("<H", data, index * 2)[0]


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    starter = root
    build = root / "build" / "animation_check"
    generated = build / "generated_animation"
    name = "AnimationCheck"
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
            str(root / "tools" / "assets" / "build_family_b_animation_bundle.py"),
            str(generated),
            "--prefix", "mobigo_clean_animation",
        ],
        check=True,
    )
    subprocess.run(
        [
            sys.executable,
            str(root / "tools" / "build" / "build_sdk_app.py"),
            str(root / "examples" / "family_b_animation_boot_demo.c"),
            "--extra-source", str(generated / "mobigo_clean_animation_resources.c"),
            "--output-dir", str(build),
            "--name", name,
            "--slot", "SY",
            "--without-system-ui",
            "--install-nand",
        ],
        check=True,
    )
    ram = build / "animation_ram.bin"
    subprocess.run(
        [
            str(emulator),
            "--rom", str(starter / "vendor" / "firmware" / "internalrom.bin"),
            "--spi", str(starter / "vendor" / "firmware" / "spi.bin"),
            "--nand", str(build / f"nand.{name}.bin"),
            "--no-window", "--steps", "245000000",
            "--dump-memory", str(ram),
            "--dump-memory-base", hex(BASE),
            "--dump-memory-words", "0x20",
        ],
        check=True,
    )
    data = ram.read_bytes()
    status = word(data, 0)
    handle = word(data, 1) | (word(data, 2) << 16)
    initial_x = word(data, 3)
    initial_record = word(data, 4)
    saw_record_1 = word(data, 5)
    record_1_x = word(data, 6)
    final_x = word(data, 7)
    final_record = word(data, 8)
    frames = word(data, 9)
    if status != 0x50A2:
        raise SystemExit(f"FAIL animation status={status:#06x}")
    if handle != 0x80000000:
        raise SystemExit(f"FAIL animation handle={handle:#010x}")
    if initial_x != 80 or initial_record != 0 or saw_record_1 != 1:
        raise SystemExit(
            f"FAIL animation initial/transition x={initial_x} record={initial_record} saw={saw_record_1}"
        )
    if record_1_x != 84 or frames <= 1:
        raise SystemExit(
            f"FAIL animation delta/frames record1_x={record_1_x} expected=84 frames={frames}"
        )
    print(
        "PASS family-B animation "
        f"handle={handle:#010x} x={initial_x}->{record_1_x} "
        f"records=0->1 final={final_record}@{final_x} frames={frames}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
