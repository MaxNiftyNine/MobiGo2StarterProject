#!/usr/bin/env python3
"""Build the clean homebrew template and verify live resident system-key edges."""

from __future__ import annotations

import struct
import subprocess
import sys
from pathlib import Path


def read_word(data: bytes, base: int, address: int) -> int:
    return struct.unpack_from("<H", data, (address - base) * 2)[0]


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    starter = root
    build = root / "build" / "homebrew_input_check"
    emulator = starter / "build" / "emulator-macos" / "mobigo2_emu"
    if not emulator.exists():
        subprocess.run([str(starter / "tools" / "build" / "emulator_macos.sh")], check=True)

    subprocess.run(
        [
            sys.executable,
            str(root / "tools" / "build" / "build_sdk_app.py"),
            str(root / "app" / "main.c"),
            "--output-dir", str(build),
            "--name", "HomebrewInputCheck",
            "--slot", "SY",
            "--install-nand",
        ],
        check=True,
    )

    ram = build / "input_check_ram.bin"
    subprocess.run(
        [
            str(emulator),
            "--rom", str(starter / "vendor" / "firmware" / "internalrom.bin"),
            "--spi", str(starter / "vendor" / "firmware" / "spi.bin"),
            "--nand", str(build / "nand.HomebrewInputCheck.bin"),
            "--no-window",
            "--steps", "266000000",
            "--key-event", "245000000,5000000,volup",
            "--key-event", "255000000,8000000,brightness",
            "--dump-memory", str(ram),
            "--dump-memory-base", "0x0058c0",
            "--dump-memory-words", "0x0020",
        ],
        check=True,
    )

    memory = ram.read_bytes()
    base = 0x58C0
    status = read_word(memory, base, base + 0)
    settings = read_word(memory, base, base + 1) | (
        read_word(memory, base, base + 2) << 16
    )
    poweroff = read_word(memory, base, base + 3) | (
        read_word(memory, base, base + 4) << 16
    )
    volume = read_word(memory, base, base + 5)
    brightness = read_word(memory, base, base + 6)
    last_key = read_word(memory, base, base + 7)

    if status != 0x6004:
        raise SystemExit(f"FAIL template status={status:#06x}")
    if settings != 0x80000000:
        raise SystemExit(f"FAIL settings handle={settings:#010x}")
    if poweroff != 0x80000001:
        raise SystemExit(f"FAIL poweroff handle={poweroff:#010x}")
    if volume != 8:
        raise SystemExit(f"FAIL Volume+ edge produced level={volume}, expected 8")
    if brightness != 3:
        raise SystemExit(
            f"FAIL held Brightness edge produced level={brightness}, expected exactly 3"
        )
    if last_key != 0x1000:
        raise SystemExit(f"FAIL last system key={last_key:#06x}, expected Brightness")

    print(
        "PASS resident-system-keys "
        f"status={status:#06x} settings={settings:#010x} "
        f"poweroff={poweroff:#010x} volume={volume} "
        f"brightness={brightness} last_key={last_key:#06x}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
