#!/usr/bin/env python3
"""Locate the common MobiGo volume and brightness lookup tables."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path


MAGIC = b"bM_gbMQa"
HEADER_WORDS = 0x800
VOLUME = (4, 14, 25, 35, 45, 55, 67, 79, 91, 105)
BRIGHTNESS = (1, 5, 10, 15)


def all_offsets(data: bytes, pattern: bytes) -> list[int]:
    result = []
    position = 0
    while True:
        position = data.find(pattern, position)
        if position < 0:
            return result
        result.append(position)
        position += 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("images", type=Path, nargs="+")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    volume_bytes = struct.pack("<10H", *VOLUME)
    brightness_bytes = struct.pack("<4H", *BRIGHTNESS)
    report = {
        "schema": 1,
        "tables": {
            "volume_logical_to_master_gain": list(VOLUME),
            "brightness_logical_to_backlight": list(BRIGHTNESS),
        },
        "images": [],
    }
    for path in args.images:
        data = path.read_bytes()
        if len(data) < 0x1000 or data[:8] != MAGIC:
            raise ValueError(f"{path}: not an MBA/GAM")
        _, _, _, entry, body_load = struct.unpack_from("<5I", data, 8)
        runtime_base = body_load - HEADER_WORDS

        def describe(offset: int) -> dict[str, int]:
            return {
                "file_offset": offset,
                "runtime_word_address": runtime_base + offset // 2,
            }

        volume_offsets = all_offsets(data, volume_bytes)
        brightness_offsets = all_offsets(data, brightness_bytes)
        report["images"].append(
            {
                "name": path.name,
                "path": str(path.resolve()),
                "sha256": hashlib.sha256(data).hexdigest(),
                "runtime_base": runtime_base,
                "entry": entry,
                "volume_matches": [describe(value) for value in volume_offsets],
                "brightness_matches": [
                    describe(value) for value in brightness_offsets
                ],
                "tables_adjacent": any(
                    brightness == volume + len(volume_bytes) + 4
                    for volume in volume_offsets
                    for brightness in brightness_offsets
                ),
            }
        )

    encoded = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
