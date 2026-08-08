#!/usr/bin/env python3
"""Generate original light-blue wave artwork as a family-A background."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "tools" / "assets"
if str(ASSETS) not in sys.path:
    sys.path.insert(0, str(ASSETS))

from build_standard_settings_bundle import (  # noqa: E402
    HEADER_WORDS,
    PALETTE_SOURCE_WORDS,
    PRIMARY_TAG,
    SECONDARY_TAG,
    WordBuilder,
    bytes_to_words,
    c_identifier,
    c_words,
    pack_2bpp,
    rgb555,
    words_to_bytes,
)


WIDTH = 320
HEIGHT = 240
CELL = 16
MAP_WORDS = 0x400
TILE_WORDS = CELL * CELL // 8


def pixel(global_x: int, global_y: int) -> int:
    first = 80 + int(14 * math.sin(global_x / 34.0))
    second = 157 + int(19 * math.sin(global_x / 47.0 + 1.1))
    if abs(global_y - first) <= 2 or abs(global_y - second) <= 2:
        return 3
    if first < global_y < first + 34 or second < global_y < second + 28:
        return 2
    if global_y > first:
        return 1
    return 0


def build_resources() -> tuple[list[int], list[int], dict[str, object]]:
    even = [rgb555(0, 0, 0)] * PALETTE_SOURCE_WORDS
    odd = [rgb555(0, 0, 0)] * PALETTE_SOURCE_WORDS
    even[:4] = [
        rgb555(6, 20, 29),
        rgb555(8, 24, 31),
        rgb555(18, 29, 31),
        rgb555(31, 31, 31),
    ]
    # The clean font uses selector 0 in the sprite palette bank.
    odd[:4] = [
        rgb555(0, 0, 0, transparent=True),
        rgb555(4, 7, 12),
        rgb555(31, 31, 31),
        rgb555(31, 18, 3),
    ]
    primary = even + odd
    tilemap_offset = len(primary)
    tilemap = [0] * MAP_WORDS
    primary.extend(tilemap)
    graphics_offset = len(primary)
    primary.extend([0] * TILE_WORDS)

    tile_index = 1
    for tile_y in range(HEIGHT // CELL):
        for tile_x in range(WIDTH // CELL):
            pixels = [
                pixel(tile_x * CELL + x, tile_y * CELL + y)
                for y in range(CELL)
                for x in range(CELL)
            ]
            primary.extend(bytes_to_words(pack_2bpp(pixels, CELL, CELL)))
            tilemap[tile_y * (WIDTH // CELL) + tile_x] = tile_index
            tile_index += 1
    primary[tilemap_offset : tilemap_offset + MAP_WORDS] = tilemap

    graph = WordBuilder()
    graph.reserve(HEADER_WORDS)
    graph.label("empty_lookup")
    graph.label("ui_a_table")
    descriptor = graph.reserve(10)
    graph.label("ui_b_empty")
    graph.label("auto_instances")
    graph.reserve(4)
    graph.label("background")
    image = graph.reserve(18)
    graph.label("runtime_slot")
    graph.add(0, 0)

    graph.set_u32(0x00, 0x80000002)
    graph.set_u32(0x02, PRIMARY_TAG)
    graph.set_u32(0x04, PRIMARY_TAG + PALETTE_SOURCE_WORDS)
    graph.set_u32(0x06, SECONDARY_TAG)
    graph.set_u32(0x08, SECONDARY_TAG + 0x100)
    graph.set_u16(0x0A, 0)
    graph.set_relative(0x0C, "empty_lookup")
    graph.set_relative(0x10, "ui_a_table")
    graph.set_u16(0x12, 1)
    graph.set_relative(0x14, "ui_a_table")
    graph.set_u16(0x16, 0)
    graph.set_relative(0x18, "ui_b_empty")
    graph.set_relative(0x1A, "auto_instances")
    graph.words[descriptor : descriptor + 10] = [
        1, 0, 0, 0, 0, 0x40, 0xFFFF, 0xFFFF, 0, 0
    ]
    graph.set_relative(descriptor + 8, "background")
    graph.words[image : image + 18] = [
        WIDTH, HEIGHT, CELL, CELL, 0, 0, HEIGHT - 1, 0, WIDTH - 1,
        0, 0, 0, 0, 0, 0, 0, 0, 0,
    ]
    graph.set_u32(image + 10, PRIMARY_TAG + graphics_offset)
    graph.set_u32(image + 12, PRIMARY_TAG + tilemap_offset)
    graph.set_relative(image + 16, "runtime_slot")
    manifest = {
        "schema": 1,
        "provenance": "Original clean-room light-blue wave artwork.",
        "bundle_word_count": len(graph.words),
        "primary_word_count": len(primary),
        "tile_count": tile_index,
    }
    return graph.words, primary, manifest


def write_outputs(output: Path, prefix: str) -> None:
    bundle, primary, manifest = build_resources()
    symbol = c_identifier(prefix)
    upper = symbol.upper()
    output.mkdir(parents=True, exist_ok=True)
    (output / "bundle.bin").write_bytes(words_to_bytes(bundle))
    (output / "primary.bin").write_bytes(words_to_bytes(primary))
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (output / f"{prefix}_resources.h").write_text(
        f"""#ifndef {upper}_RESOURCES_H
#define {upper}_RESOURCES_H
#include "mobigo_sdk/resident_resources.h"
enum {{ {upper}_BUNDLE_WORD_COUNT = {len(bundle)} }};
extern const unsigned short {symbol}_bundle_template[{len(bundle)}];
extern const unsigned short {symbol}_primary_words[{len(primary)}];
void {symbol}_copy_bundle(unsigned short *destination);
void {symbol}_register(unsigned short *writable_bundle);
mg_sdk_ui_handle {symbol}_create(void);
#endif
""",
        encoding="ascii",
    )
    (output / f"{prefix}_resources.c").write_text(
        f"""#include "{prefix}_resources.h"
const unsigned short {symbol}_bundle_template[{len(bundle)}] = {{
{c_words(bundle)}
}};
const unsigned short {symbol}_primary_words[{len(primary)}] = {{
{c_words(primary)}
}};
void {symbol}_copy_bundle(unsigned short *destination)
{{
    unsigned short index;
    for (index = 0; index < {upper}_BUNDLE_WORD_COUNT; ++index)
        destination[index] = {symbol}_bundle_template[index];
}}
void {symbol}_register(unsigned short *writable_bundle)
{{
    mg_sdk_resident_register_asset_bundle(
        writable_bundle, (void *){symbol}_primary_words, (void *)0);
}}
mg_sdk_ui_handle {symbol}_create(void)
{{
    return mg_sdk_ui_a_create(0);
}}
""",
        encoding="ascii",
    )
    print(
        f"PASS wave bundle_words={len(bundle)} primary_words={len(primary)} "
        f"output={output}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--prefix", default="hb_wave")
    args = parser.parse_args()
    write_outputs(args.output, args.prefix)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

