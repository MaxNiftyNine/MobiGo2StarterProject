#!/usr/bin/env python3
"""Build and verify the clean-room dynamic font through the resident renderer."""

from __future__ import annotations

import struct
import subprocess
import sys
from collections import Counter
from pathlib import Path


def read_word(data: bytes, base: int, address: int) -> int:
    return struct.unpack_from("<H", data, (address - base) * 2)[0]


def read_bmp_rgb(path: Path) -> tuple[int, int, list[tuple[int, int, int]]]:
    """Read an uncompressed 32-bit BMP without third-party dependencies."""
    data = path.read_bytes()
    if len(data) < 54 or data[:2] != b"BM":
        raise ValueError(f"not a BMP file: {path}")

    pixel_offset = struct.unpack_from("<I", data, 10)[0]
    dib_size = struct.unpack_from("<I", data, 14)[0]
    if dib_size < 40:
        raise ValueError(f"unsupported BMP DIB header size {dib_size}")

    width, signed_height = struct.unpack_from("<ii", data, 18)
    planes, bits_per_pixel = struct.unpack_from("<HH", data, 26)
    compression = struct.unpack_from("<I", data, 30)[0]
    if width <= 0 or signed_height == 0:
        raise ValueError(f"invalid BMP dimensions {width}x{signed_height}")
    if planes != 1 or bits_per_pixel != 32 or compression != 0:
        raise ValueError(
            "expected an uncompressed 32-bit BMP, got "
            f"planes={planes} bpp={bits_per_pixel} compression={compression}"
        )

    height = abs(signed_height)
    row_bytes = width * 4
    required_size = pixel_offset + row_bytes * height
    if len(data) < required_size:
        raise ValueError(
            f"truncated BMP: need {required_size} bytes, got {len(data)}"
        )

    rows: list[list[tuple[int, int, int]]] = []
    for row_index in range(height):
        row_start = pixel_offset + row_index * row_bytes
        row: list[tuple[int, int, int]] = []
        for column in range(width):
            blue, green, red, _alpha = struct.unpack_from(
                "<BBBB", data, row_start + column * 4
            )
            row.append((red, green, blue))
        rows.append(row)

    if signed_height > 0:
        rows.reverse()
    return width, height, [pixel for row in rows for pixel in row]


def build_app(root: Path, source: Path, out: Path, name: str) -> None:
    subprocess.run(
        [
            sys.executable,
            str(root / "tools" / "build" / "build_sdk_app.py"),
            str(source),
            "--output-dir", str(out),
            "--name", name,
            "--slot", "SY",
            "--with-clean-font",
            "--install-nand",
        ],
        check=True,
    )


def run_app(
    root: Path, out: Path, name: str
) -> tuple[bytes, tuple[int, int, list[tuple[int, int, int]]]]:
    starter = root
    emulator = starter / "build" / "emulator-macos" / "mobigo2_emu"
    if not emulator.exists():
        subprocess.run(
            [str(starter / "tools" / "build" / "emulator_macos.sh")],
            check=True,
        )

    ram = out / "font_ram.bin"
    frame = out / "font_frame.bmp"
    subprocess.run(
        [
            str(emulator),
            "--rom", str(starter / "vendor" / "firmware" / "internalrom.bin"),
            "--spi", str(starter / "vendor" / "firmware" / "spi.bin"),
            "--nand", str(out / f"nand.{name}.bin"),
            "--no-window",
            "--steps", "250000000",
            "--dump-memory", str(ram),
            "--dump-memory-base", "0x60f0",
            "--dump-memory-words", "0x20",
            "--dump-frame", str(frame),
        ],
        check=True,
    )
    return ram.read_bytes(), read_bmp_rgb(frame)


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    baseline = root / "build" / "font_check_baseline"
    demo = root / "build" / "font_check_demo"

    build_app(
        root,
        root / "examples" / "font_dynamic_baseline.c",
        baseline,
        "FontCheckBaseline",
    )
    build_app(
        root,
        root / "examples" / "font_dynamic_boot_demo.c",
        demo,
        "FontCheckDemo",
    )

    baseline_ram, baseline_frame = run_app(
        root, baseline, "FontCheckBaseline"
    )
    demo_ram, demo_frame = run_app(root, demo, "FontCheckDemo")
    base = 0x60F0

    if read_word(baseline_ram, base, base) != 0x7612:
        raise SystemExit("FAIL font baseline did not reach resident frame loop")
    if read_word(baseline_ram, base, base + 1) != 1:
        raise SystemExit("FAIL font baseline dynamic slot is not 1")
    if read_word(demo_ram, base, base) != 0x7604:
        raise SystemExit("FAIL font demo did not reach resident frame loop")
    if read_word(demo_ram, base, base + 1) != 1:
        raise SystemExit("FAIL font demo dynamic slot is not 1")

    first_handle = (
        read_word(demo_ram, base, base + 2)
        | (read_word(demo_ram, base, base + 3) << 16)
    )
    last_handle = (
        read_word(demo_ram, base, base + 4)
        | (read_word(demo_ram, base, base + 5) << 16)
    )
    if first_handle != 0x80000000 or last_handle != 0x80000007:
        raise SystemExit(
            "FAIL font family-B handles "
            f"first={first_handle:#010x} last={last_handle:#010x}"
        )

    baseline_width, baseline_height, baseline_pixels = baseline_frame
    demo_width, demo_height, demo_pixels = demo_frame
    if (baseline_width, baseline_height) != (demo_width, demo_height):
        raise SystemExit("FAIL font frames have different dimensions")
    width = baseline_width
    changed = [
        index
        for index, (before, after) in enumerate(
            zip(baseline_pixels, demo_pixels)
        )
        if before != after
    ]
    if len(changed) != 112:
        raise SystemExit(
            f"FAIL font changed-pixel count={len(changed)}, expected 112"
        )

    xs = [index % width for index in changed]
    ys = [index // width for index in changed]
    bbox = (min(xs), min(ys), max(xs), max(ys))
    bbox_width = bbox[2] - bbox[0] + 1
    bbox_height = bbox[3] - bbox[1] + 1
    if (bbox_width, bbox_height) != (53, 7):
        raise SystemExit(
            "FAIL font changed geometry "
            f"bbox={bbox} size={(bbox_width, bbox_height)}"
        )

    before_colors = Counter(baseline_pixels[index] for index in changed)
    after_colors = Counter(demo_pixels[index] for index in changed)
    if before_colors != Counter({(0, 0, 0): 112}):
        raise SystemExit(f"FAIL font baseline colors={before_colors}")
    if after_colors != Counter({(255, 255, 255): 112}):
        raise SystemExit(f"FAIL font rendered colors={after_colors}")

    print(
        "PASS dynamic-font "
        f"slot=1 handles={first_handle:#010x}..{last_handle:#010x} "
        f"changed_pixels=112 bbox={bbox} size=53x7 color=white"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
