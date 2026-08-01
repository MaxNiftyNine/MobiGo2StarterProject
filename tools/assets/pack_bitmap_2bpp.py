#!/usr/bin/env python3
"""Pack a four-index PGM image into the standard MobiGo 2 2-bpp layout."""

from __future__ import annotations

import argparse
from pathlib import Path


def _tokens(data: bytes):
    for line in data.splitlines():
        line = line.split(b"#", 1)[0]
        yield from line.split()


def read_pgm(path: Path) -> tuple[int, int, list[int]]:
    data = path.read_bytes()
    if data.startswith(b"P2"):
        values = list(_tokens(data))
        if len(values) < 4 or values[0] != b"P2":
            raise ValueError("invalid P2 PGM")
        width, height, maximum = map(int, values[1:4])
        pixels = [int(value) for value in values[4:]]
    elif data.startswith(b"P5"):
        cursor = 2
        header: list[bytes] = []
        while len(header) < 3:
            while cursor < len(data) and chr(data[cursor]).isspace():
                cursor += 1
            if cursor < len(data) and data[cursor] == ord("#"):
                cursor = data.find(b"\n", cursor)
                if cursor < 0:
                    raise ValueError("truncated P5 PGM comment")
                continue
            end = cursor
            while end < len(data) and not chr(data[end]).isspace():
                end += 1
            header.append(data[cursor:end])
            cursor = end
        width, height, maximum = map(int, header)
        while cursor < len(data) and chr(data[cursor]).isspace():
            cursor += 1
        if maximum > 255:
            raise ValueError("16-bit P5 PGM is not supported")
        pixels = list(data[cursor:])
    else:
        raise ValueError("input must be a P2 or P5 PGM")

    if width <= 0 or height <= 0 or len(pixels) != width * height:
        raise ValueError("PGM dimensions do not match its pixel count")
    if maximum != 3 or any(pixel < 0 or pixel > 3 for pixel in pixels):
        raise ValueError("PGM max value and all indices must be 0..3")
    return width, height, pixels


def pack_indices(width: int, height: int, pixels: list[int]) -> bytes:
    if width <= 0 or height <= 0 or width % 4:
        raise ValueError("width must be a positive multiple of four")
    if len(pixels) != width * height:
        raise ValueError("pixel count does not match dimensions")
    if any(pixel < 0 or pixel > 3 for pixel in pixels):
        raise ValueError("pixel index is outside 0..3")
    result = bytearray()
    for offset in range(0, len(pixels), 4):
        a, b, c, d = pixels[offset : offset + 4]
        result.append((a << 6) | (b << 4) | (c << 2) | d)
    return bytes(result)


def unpack_indices(width: int, height: int, packed: bytes) -> list[int]:
    if width <= 0 or height <= 0 or width % 4:
        raise ValueError("width must be a positive multiple of four")
    if len(packed) != width * height // 4:
        raise ValueError("packed length does not match dimensions")
    result: list[int] = []
    for value in packed:
        result.extend(
            ((value >> 6) & 3, (value >> 4) & 3, (value >> 2) & 3, value & 3)
        )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="P2/P5 PGM with max value 3")
    parser.add_argument("output", type=Path, help="packed binary output")
    args = parser.parse_args()
    width, height, pixels = read_pgm(args.input)
    packed = pack_indices(width, height, pixels)
    args.output.write_bytes(packed)
    print(
        f"packed {width}x{height} indices into {len(packed)} bytes "
        f"({len(packed) // 2} u'nSP words)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
