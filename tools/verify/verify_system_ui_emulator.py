#!/usr/bin/env python3
"""Build and execute the combined clean-room system-UI demo in the emulator."""

from __future__ import annotations

import shutil
import struct
import subprocess
import sys
from pathlib import Path


def read_word(data: bytes, base: int, address: int) -> int:
    return struct.unpack_from("<H", data, (address - base) * 2)[0]


def read_bmp_pixels(path: Path) -> tuple[int, int, list[tuple[int, int, int]]]:
    data = path.read_bytes()
    if data[:2] != b"BM":
        raise ValueError("emulator frame is not a BMP")
    pixel_offset = struct.unpack_from("<I", data, 10)[0]
    width = struct.unpack_from("<i", data, 18)[0]
    signed_height = struct.unpack_from("<i", data, 22)[0]
    bits_per_pixel = struct.unpack_from("<H", data, 28)[0]
    compression = struct.unpack_from("<I", data, 30)[0]
    if width <= 0 or signed_height == 0 or bits_per_pixel != 32 or compression != 0:
        raise ValueError("unexpected emulator BMP format")
    height = abs(signed_height)
    top_down = signed_height < 0
    stride = width * 4
    pixels: list[tuple[int, int, int]] = []
    for y in range(height):
        source_y = y if top_down else height - 1 - y
        row = pixel_offset + source_y * stride
        for x in range(width):
            b, g, r, _ = data[row + x * 4 : row + x * 4 + 4]
            pixels.append((r, g, b))
    return width, height, pixels


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    starter = root
    build = root / "build" / "system_ui_demo"
    generated = build / "generated_system_ui"
    name = "SystemUiDemo"
    emulator = starter / "build" / "emulator-macos" / "mobigo2_emu"
    if not emulator.exists():
        subprocess.run([str(starter / "tools" / "build" / "emulator_macos.sh")], check=True)

    if build.exists():
        shutil.rmtree(build)
    subprocess.run(
        [
            sys.executable,
            str(root / "tools" / "assets" / "build_system_ui_bundle.py"),
            str(generated),
            "--prefix", "mobigo_clean_system_ui",
        ],
        check=True,
    )
    subprocess.run(
        [
            sys.executable,
            str(root / "tools" / "build" / "build_sdk_app.py"),
            str(root / "examples" / "system_ui_generated_boot_demo.c"),
            "--extra-source",
            str(generated / "mobigo_clean_system_ui_resources.c"),
            "--output-dir", str(build),
            "--name", name,
            "--slot", "SY",
            "--without-system-ui",
            "--install-nand",
        ],
        check=True,
    )

    frame = build / "verification_frame.bmp"
    ram = build / "verification_app_ram.bin"
    log = build / "verification_emulator.log"
    subprocess.run(
        [
            str(emulator),
            "--rom", str(starter / "vendor" / "firmware" / "internalrom.bin"),
            "--spi", str(starter / "vendor" / "firmware" / "spi.bin"),
            "--nand", str(build / f"nand.{name}.bin"),
            "--no-window",
            "--steps", "245000000",
            "--dump-frame", str(frame),
            "--dump-memory", str(ram),
            "--dump-memory-base", "0x005000",
            "--dump-memory-words", "0x0a00",
            "--log",
            "--log-file", str(log),
        ],
        check=True,
    )

    memory = ram.read_bytes()
    status = read_word(memory, 0x5000, 0x58F0)
    settings = read_word(memory, 0x5000, 0x58F1) | (
        read_word(memory, 0x5000, 0x58F2) << 16
    )
    poweroff = read_word(memory, 0x5000, 0x58F3) | (
        read_word(memory, 0x5000, 0x58F4) << 16
    )
    if status != 0x5004:
        raise SystemExit(f"FAIL demo status={status:#06x}")
    if settings != 0x80000000:
        raise SystemExit(f"FAIL settings handle={settings:#010x}")
    if poweroff != 0x80000001:
        raise SystemExit(f"FAIL poweroff handle={poweroff:#010x}")

    width, height, pixels = read_bmp_pixels(frame)
    nonblack = [
        (index % width, index // width, pixel)
        for index, pixel in enumerate(pixels)
        if pixel != (0, 0, 0)
    ]
    if not nonblack:
        raise SystemExit("FAIL resident renderer produced an all-black frame")
    bbox = (
        min(item[0] for item in nonblack),
        min(item[1] for item in nonblack),
        max(item[0] for item in nonblack),
        max(item[1] for item in nonblack),
    )
    unique = sorted({item[2] for item in nonblack})
    if (width, height) != (320, 240):
        raise SystemExit(f"FAIL frame dimensions={(width, height)}")
    if bbox != (77, 107, 234, 229):
        raise SystemExit(f"FAIL combined UI bbox={bbox}")
    if len(nonblack) != 1161:
        raise SystemExit(f"FAIL nonblack pixels={len(nonblack)}")

    print(
        "PASS resident-system-ui "
        f"status={status:#06x} settings={settings:#010x} "
        f"poweroff={poweroff:#010x} bbox={bbox} "
        f"nonblack={len(nonblack)} colors={unique}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
