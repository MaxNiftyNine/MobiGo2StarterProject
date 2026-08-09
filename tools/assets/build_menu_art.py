#!/usr/bin/env python3
"""Build a 64x104 MBA menu icon and RGB555 palette from a portable PPM image."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
import struct
import sys


ROOT = Path(__file__).resolve().parents[2]
BUILD_TOOLS = ROOT / "tools" / "build"
if str(BUILD_TOOLS) not in sys.path:
    sys.path.insert(0, str(BUILD_TOOLS))

from build_mba import (  # noqa: E402
    TILE_HEIGHT,
    TILE_WIDTH,
    default_menu_tile,
    default_palette,
    rgb555,
)


TRANSPARENT_KEY = (255, 0, 255)


def read_ppm(path: Path) -> tuple[int, int, list[tuple[int, int, int]]]:
    data = path.read_bytes()
    tokens: list[bytes] = []
    index = 0
    while len(tokens) < 4:
        while index < len(data) and data[index] in b" \t\r\n":
            index += 1
        if index < len(data) and data[index] == ord("#"):
            while index < len(data) and data[index] not in b"\r\n":
                index += 1
            continue
        start = index
        while index < len(data) and data[index] not in b" \t\r\n#":
            index += 1
        if start == index:
            raise ValueError("invalid PPM header")
        tokens.append(data[start:index])
    if tokens[0] != b"P6":
        raise ValueError("menu icon must be a binary P6 PPM image")
    width, height, maximum = (int(value) for value in tokens[1:])
    if width < 1 or height < 1 or maximum != 255:
        raise ValueError("PPM must have positive dimensions and max value 255")
    if data[index:index + 2] == b"\r\n":
        index += 2
    elif index < len(data) and data[index] in b" \t\r\n":
        index += 1
    raw = data[index:]
    if len(raw) != width * height * 3:
        raise ValueError("PPM raster length does not match its dimensions")
    pixels = [tuple(raw[offset:offset + 3]) for offset in range(0, len(raw), 3)]
    return width, height, pixels  # type: ignore[return-value]


def fit_pixels(
    width: int,
    height: int,
    pixels: list[tuple[int, int, int]],
) -> list[tuple[int, int, int] | None]:
    scale = min(TILE_WIDTH / width, TILE_HEIGHT / height)
    output_width = max(1, min(TILE_WIDTH, int(width * scale + 0.5)))
    output_height = max(1, min(TILE_HEIGHT, int(height * scale + 0.5)))
    left = (TILE_WIDTH - output_width) // 2
    top = (TILE_HEIGHT - output_height) // 2
    output: list[tuple[int, int, int] | None] = [None] * (TILE_WIDTH * TILE_HEIGHT)
    for y in range(output_height):
        source_y = min(height - 1, y * height // output_height)
        for x in range(output_width):
            source_x = min(width - 1, x * width // output_width)
            color = pixels[source_y * width + source_x]
            if color != TRANSPARENT_KEY:
                output[(top + y) * TILE_WIDTH + left + x] = color
    return output


def distance(left: tuple[int, int, int], right: tuple[int, int, int]) -> int:
    return sum((a - b) * (a - b) for a, b in zip(left, right))


def choose_colors(pixels: list[tuple[int, int, int] | None]) -> list[tuple[int, int, int]]:
    counts = Counter(pixel for pixel in pixels if pixel is not None)
    if not counts:
        return [(0, 0, 0)]
    ordered = sorted(counts, key=lambda color: (-counts[color], color))
    if len(ordered) <= 15:
        return ordered

    centers = [ordered[0]]
    while len(centers) < 15:
        centers.append(max(
            ordered,
            key=lambda color: counts[color] * min(distance(color, item) for item in centers),
        ))
    for _ in range(8):
        groups = [[0, 0, 0, 0] for _ in centers]
        for color, count in counts.items():
            selected = min(range(len(centers)), key=lambda item: distance(color, centers[item]))
            group = groups[selected]
            group[0] += color[0] * count
            group[1] += color[1] * count
            group[2] += color[2] * count
            group[3] += count
        updated = [
            center if group[3] == 0 else (
                group[0] // group[3], group[1] // group[3], group[2] // group[3]
            )
            for center, group in zip(centers, groups)
        ]
        if updated == centers:
            break
        centers = updated
    return centers


def convert(source: Path) -> tuple[bytes, bytes]:
    width, height, source_pixels = read_ppm(source)
    pixels = fit_pixels(width, height, source_pixels)
    colors = choose_colors(pixels)
    palette_words = [rgb555(0, 0, 0, transparent=True)]
    palette_words.extend(rgb555(*color) for color in colors)
    palette_words.extend([rgb555(0, 0, 0)] * (16 - len(palette_words)))
    indices = []
    for pixel in pixels:
        indices.append(
            0 if pixel is None else 1 + min(
                range(len(colors)), key=lambda item: distance(pixel, colors[item])
            )
        )
    tile = bytearray(TILE_WIDTH * TILE_HEIGHT // 2)
    for offset in range(0, len(indices), 2):
        tile[offset // 2] = (indices[offset] << 4) | indices[offset + 1]
    return bytes(tile), struct.pack("<16H", *palette_words)


def write_default_source(path: Path) -> None:
    palette = struct.unpack("<16H", default_palette())
    tile = default_menu_tile()
    raster = bytearray()
    for byte in tile:
        for index in (byte >> 4, byte & 15):
            value = palette[index]
            if value & 0x8000:
                raster.extend(TRANSPARENT_KEY)
            else:
                raster.extend((
                    ((value >> 10) & 31) * 255 // 31,
                    ((value >> 5) & 31) * 255 // 31,
                    (value & 31) * 255 // 31,
                ))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(f"P6\n{TILE_WIDTH} {TILE_HEIGHT}\n255\n".encode("ascii") + raster)


def write(output: Path, source: Path | None = None) -> None:
    output.mkdir(parents=True, exist_ok=True)
    tile, palette = (
        convert(source) if source is not None
        else (default_menu_tile(), default_palette())
    )
    (output / "menu_tile.bin").write_bytes(tile)
    (output / "menu_palette.bin").write_bytes(palette)
    detail = f" source={source}" if source is not None else ""
    print(f"PASS baked MBA menu art output={output}{detail}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--source", type=Path, help="P6 PPM; #ff00ff pixels are transparent")
    parser.add_argument("--write-default-source", type=Path)
    args = parser.parse_args()
    if args.write_default_source is not None:
        write_default_source(args.write_default_source)
    write(args.output, args.source)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
