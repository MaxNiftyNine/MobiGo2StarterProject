#!/usr/bin/env python3
"""Convert the ccleste BMP/map assets to const unSP word arrays."""

from pathlib import Path
import re

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "reference"
OUTPUT = ROOT / "src" / "assets.h"


def emit_array(name: str, values: list[int], width: int = 16) -> str:
    lines = [f"static const unsigned short {name}[{len(values)}] = {{"]
    for offset in range(0, len(values), width):
        chunk = values[offset : offset + width]
        lines.append("    " + ",".join(f"0x{value:02x}" for value in chunk) + ",")
    lines.append("};")
    return "\n".join(lines)


def pack_nibbles(values: list[int]) -> list[int]:
    packed = []
    for offset in range(0, len(values), 4):
        word = 0
        for index, value in enumerate(values[offset : offset + 4]):
            word |= (value & 15) << (index * 4)
        packed.append(word)
    return packed


def pack_bytes(values: list[int]) -> list[int]:
    return [
        values[offset] | ((values[offset + 1] if offset + 1 < len(values) else 0) << 8)
        for offset in range(0, len(values), 2)
    ]


def pack_bits(values: list[int]) -> list[int]:
    packed = []
    for offset in range(0, len(values), 16):
        word = 0
        for index, value in enumerate(values[offset : offset + 16]):
            if value:
                word |= 1 << index
        packed.append(word)
    return packed


def extract_initializer(text: str, name: str) -> list[int]:
    match = re.search(rf"{name}[^=]*=\s*\{{(.*?)\}}\s*;", text, re.S)
    if not match:
        raise RuntimeError(f"could not locate {name}")
    values = re.findall(r"0x[0-9a-fA-F]+|\b\d+\b", match.group(1))
    return [int(value, 16) if value.lower().startswith("0x") else int(value, 10) for value in values]


def main() -> None:
    gfx = list(Image.open(REFERENCE / "gfx.bmp").getdata())
    font = list(Image.open(REFERENCE / "font.bmp").getdata())
    tilemap_source = (REFERENCE / "tilemap.h").read_text()
    tilemap = extract_initializer(tilemap_source, "tilemap_data")
    flags = extract_initializer(tilemap_source, "tile_flags")
    if len(gfx) != 128 * 64 or len(font) != 128 * 85:
        raise RuntimeError("unexpected bitmap dimensions")
    if len(tilemap) != 8192 or len(flags) != 128:
        raise RuntimeError("unexpected map dimensions")

    output = [
        "#ifndef CELESTE_MOBIGO_ASSETS_H",
        "#define CELESTE_MOBIGO_ASSETS_H",
        "",
        emit_array("celeste_gfx_packed", pack_nibbles(gfx)),
        "",
        emit_array("celeste_font_packed", pack_bits(font)),
        "",
        emit_array("celeste_tilemap_packed", pack_bytes(tilemap)),
        "",
        emit_array("celeste_tile_flags_packed", pack_bytes(flags)),
        "",
        "#endif",
        "",
    ]
    OUTPUT.write_text("\n".join(output))


if __name__ == "__main__":
    main()
