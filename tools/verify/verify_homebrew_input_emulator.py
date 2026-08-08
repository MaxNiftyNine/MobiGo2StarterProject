#!/usr/bin/env python3
"""Verify the starter's automatic resident system controls in Emulator2."""

from __future__ import annotations

import struct
import subprocess
import sys
from pathlib import Path

from emulator_support import find_emulator, mba_overlay_arguments


CONTROLS_BASE = 0x5800
# These are part of the verified bundled NAND fixture. The standard-controls
# adapter must load them rather than its fallback defaults before applying the
# two injected edges below.
FIXTURE_VOLUME = 3
FIXTURE_BRIGHTNESS = 1


def read_word(data: bytes, base: int, address: int) -> int:
    return struct.unpack_from("<H", data, (address - base) * 2)[0]


def run_starter(
    root: Path,
    emulator: Path,
    mba: Path,
    dump: Path,
    *,
    steps: int,
    events: tuple[str, ...],
) -> tuple[bytes, str]:
    command = [
        str(emulator),
        "--rom", str(root / "vendor" / "firmware" / "internalrom.bin"),
        "--spi", str(root / "vendor" / "firmware" / "spi.bin"),
        *mba_overlay_arguments(root, mba),
        "--no-window",
        "--steps", str(steps),
        "--dump-memory", str(dump),
        "--dump-memory-base", hex(CONTROLS_BASE),
        "--dump-memory-words", "0x20",
    ]
    for event in events:
        command.extend(("--key-event", event))
    result = subprocess.run(
        command,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if result.returncode:
        raise SystemExit(
            f"FAIL emulator exited with {result.returncode}:\n{result.stdout}"
        )
    return dump.read_bytes(), result.stdout


def decode_controls(memory: bytes) -> dict[str, int]:
    base = CONTROLS_BASE
    return {
        "backend": read_word(memory, base, base) |
            (read_word(memory, base, base + 1) << 16),
        "user": read_word(memory, base, base + 2) |
            (read_word(memory, base, base + 3) << 16),
        "volume": read_word(memory, base, base + 4),
        "brightness": read_word(memory, base, base + 5),
        "overlay_visible": read_word(memory, base, base + 6),
        "settings": read_word(memory, base, base + 13) |
            (read_word(memory, base, base + 14) << 16),
        "poweroff": read_word(memory, base, base + 15) |
            (read_word(memory, base, base + 16) << 16),
        "initialized": read_word(memory, base, base + 17),
        "last_key": read_word(memory, base, base + 18),
    }


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    starter = root
    build = root / "build" / "homebrew_input_check"
    emulator = find_emulator(starter)

    subprocess.run(
        [
            sys.executable,
            str(root / "tools" / "build" / "build_sdk_app.py"),
            str(root / "app" / "main.c"),
            "--output-dir", str(build),
            "--name", "HomebrewInputCheck",
            "--slot", "SY",
        ],
        check=True,
    )

    mba = build / "HomebrewInputCheck.MBA"
    memory, output = run_starter(
        root,
        emulator,
        mba,
        build / "input_check_ram.bin",
        steps=400_000_000,
        events=(
            "245000000,5000000,volup",
            "255000000,8000000,brightness",
        ),
    )
    controls = decode_controls(memory)
    if controls["backend"] == 0 or controls["user"] != CONTROLS_BASE:
        raise SystemExit(
            "FAIL controls backend/user="
            f"{controls['backend']:#010x}/{controls['user']:#010x}\n{output}"
        )
    if controls["settings"] != 0x80000000:
        raise SystemExit(f"FAIL settings handle={controls['settings']:#010x}")
    if controls["poweroff"] != 0x80000001:
        raise SystemExit(f"FAIL poweroff handle={controls['poweroff']:#010x}")
    if controls["initialized"] != 1:
        raise SystemExit(
            f"FAIL standard-controls initialized={controls['initialized']}"
        )
    expected_volume = min(FIXTURE_VOLUME + 1, 9)
    if controls["volume"] != expected_volume:
        raise SystemExit(
            "FAIL resident-loaded Volume+ edge produced "
            f"level={controls['volume']}, expected {expected_volume}"
        )
    expected_brightness = (FIXTURE_BRIGHTNESS + 1) % 4
    if controls["brightness"] != expected_brightness:
        raise SystemExit(
            "FAIL resident-loaded held Brightness edge produced "
            f"level={controls['brightness']}, expected exactly {expected_brightness}"
        )
    if controls["last_key"] != 0x1000:
        raise SystemExit(
            f"FAIL last system key={controls['last_key']:#06x}, expected Brightness"
        )
    if controls["overlay_visible"] != 0:
        raise SystemExit(
            "FAIL settings overlay did not hide after the verified timeout: "
            f"visibility={controls['overlay_visible']}"
        )

    _off_memory, off_output = run_starter(
        root,
        emulator,
        mba,
        build / "off_check_ram.bin",
        steps=300_000_000,
        events=("245000000,5000000,off",),
    )
    if "Power state: off" not in off_output:
        raise SystemExit(
            "FAIL Off did not reach the emulator's powered-off terminal state:\n"
            + off_output
        )

    print(
        "PASS automatic resident-system-controls "
        f"settings={controls['settings']:#010x} "
        f"poweroff={controls['poweroff']:#010x} "
        f"volume={FIXTURE_VOLUME}->{controls['volume']} "
        f"brightness={FIXTURE_BRIGHTNESS}->{controls['brightness']} "
        "overlay_timeout=pass poweroff=pass watchdog=pass"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
