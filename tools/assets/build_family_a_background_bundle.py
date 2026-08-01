#!/usr/bin/env python3
"""Build an original version-2 bundle containing one family-A background.

The generated resource exercises the renderer-confirmed family-A grammar:
10-word descriptor -> 18-word tiled-image record -> private two-word runtime
slot.  Artwork and palette values are generated from scratch; no retail asset
payload is read by this tool.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from build_standard_settings_bundle import (
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
CELL_WIDTH = 16
CELL_HEIGHT = 16
FORMAT_2BPP = 0
PALETTE_SELECTOR = 0
# Deliberately over-provisioned source map. The recovered renderer copies only
# the region it needs into a resident-allocated PPU tilemap.
TILEMAP_SOURCE_WORDS = 0x400
TILE_WORDS_2BPP = CELL_WIDTH * CELL_HEIGHT // 8
GRAPHICS_TILE_COUNT = 2


def patterned_tile() -> list[int]:
    pixels: list[int] = []
    for y in range(CELL_HEIGHT):
        for x in range(CELL_WIDTH):
            border = x in (0, CELL_WIDTH - 1) or y in (0, CELL_HEIGHT - 1)
            diagonal = ((x + y) // 4) & 1
            pixels.append(3 if border else 1 + diagonal)
    return bytes_to_words(pack_2bpp(pixels, CELL_WIDTH, CELL_HEIGHT))


def build_resources() -> tuple[list[int], list[int], dict[str, object]]:
    even_palette = [rgb555(0, 0, 0)] * PALETTE_SOURCE_WORDS
    odd_palette = [rgb555(0, 0, 0)] * PALETTE_SOURCE_WORDS
    even_palette[:4] = [
        rgb555(1, 2, 5),
        rgb555(4, 10, 22),
        rgb555(7, 20, 28),
        rgb555(31, 28, 8),
    ]
    primary = even_palette + odd_palette

    tilemap_offset = len(primary)
    primary.extend([1] * TILEMAP_SOURCE_WORDS)
    graphics_offset = len(primary)
    primary.extend([0] * TILE_WORDS_2BPP)
    tile = patterned_tile()
    if len(tile) != TILE_WORDS_2BPP:
        raise ValueError("unexpected generated tile size")
    primary.extend(tile)

    graph = WordBuilder()
    graph.reserve(HEADER_WORDS)
    graph.label("empty_lookup")
    graph.label("ui_a_table")
    descriptor_offset = graph.reserve(10)
    graph.label("ui_b_empty")
    graph.label("auto_instance_table")
    graph.label("generated_handles")
    graph.reserve(4)
    graph.label("background_image")
    image_offset = graph.reserve(18)
    graph.label("background_runtime_slot")
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
    graph.set_relative(0x1A, "generated_handles")

    descriptor = [
        1,
        0,
        0,
        0,
        0,
        0x40,
        0xFFFF,
        0xFFFF,
        0,
        0,
    ]
    graph.words[descriptor_offset : descriptor_offset + 10] = descriptor
    graph.set_relative(descriptor_offset + 8, "background_image")

    image = [
        WIDTH,
        HEIGHT,
        CELL_WIDTH,
        CELL_HEIGHT,
        FORMAT_2BPP,
        0,
        HEIGHT - 1,
        0,
        WIDTH - 1,
        0,
        0,
        0,
        0,
        0,
        PALETTE_SELECTOR,
        0,
        0,
        0,
    ]
    graph.words[image_offset : image_offset + 18] = image
    graph.set_u32(image_offset + 10, PRIMARY_TAG + graphics_offset)
    graph.set_u32(image_offset + 12, PRIMARY_TAG + tilemap_offset)
    graph.set_relative(image_offset + 16, "background_runtime_slot")

    manifest: dict[str, object] = {
        "schema": 1,
        "provenance": "Clean-room structure and original generated artwork.",
        "address_unit": "16-bit words",
        "bundle_version": "0x80000002",
        "bundle_word_count": len(graph.words),
        "primary_word_count": len(primary),
        "family_a_descriptor": 0,
        "image": {
            "width": WIDTH,
            "height": HEIGHT,
            "cell_width": CELL_WIDTH,
            "cell_height": CELL_HEIGHT,
            "format": FORMAT_2BPP,
            "palette_selector": PALETTE_SELECTOR,
            "tilemap_primary_word_offset": f"{tilemap_offset:#06x}",
            "tilemap_word_count": TILEMAP_SOURCE_WORDS,
            "graphics_primary_word_offset": f"{graphics_offset:#06x}",
            "graphics_tile_count": GRAPHICS_TILE_COUNT,
            "graphics_words_per_tile": TILE_WORDS_2BPP,
        },
    }
    return graph.words, primary, manifest


def write_c_output(output: Path, prefix: str, bundle: list[int], primary: list[int]) -> None:
    symbol = c_identifier(prefix)
    guard = f"{symbol.upper()}_FAMILY_A_BACKGROUND_RESOURCES_H"
    (output / f"{prefix}_resources.h").write_text(
        f"""#ifndef {guard}\n#define {guard}\n\n#include \"mobigo_sdk/resident_resources.h\"\n\nenum {{\n    {symbol.upper()}_FAMILY_A_DESCRIPTOR = 0,\n    {symbol.upper()}_BUNDLE_WORD_COUNT = {len(bundle)},\n    {symbol.upper()}_PRIMARY_WORD_COUNT = {len(primary)}\n}};\n\nextern const unsigned short {symbol}_bundle_template[{len(bundle)}];\nextern const unsigned short {symbol}_primary_words[{len(primary)}];\n\nvoid {symbol}_copy_bundle(unsigned short *destination);\nvoid {symbol}_register(unsigned short *writable_bundle);\nmg_sdk_ui_handle {symbol}_create(void);\n\n#endif\n""",
        encoding="ascii",
    )
    (output / f"{prefix}_resources.c").write_text(
        f"""#include \"{prefix}_resources.h\"\n\nconst unsigned short {symbol}_bundle_template[{len(bundle)}] = {{\n{c_words(bundle)}\n}};\n\nconst unsigned short {symbol}_primary_words[{len(primary)}] = {{\n{c_words(primary)}\n}};\n\nvoid {symbol}_copy_bundle(unsigned short *destination)\n{{\n    unsigned short index;\n    for (index = 0; index < {symbol.upper()}_BUNDLE_WORD_COUNT; ++index) {{\n        destination[index] = {symbol}_bundle_template[index];\n    }}\n}}\n\nvoid {symbol}_register(unsigned short *writable_bundle)\n{{\n    mg_sdk_resident_register_asset_bundle(\n        writable_bundle,\n        (void *){symbol}_primary_words,\n        (void *)0);\n}}\n\nmg_sdk_ui_handle {symbol}_create(void)\n{{\n    return mg_sdk_ui_a_create({symbol.upper()}_FAMILY_A_DESCRIPTOR);\n}}\n""",
        encoding="ascii",
    )


def write_outputs(output: Path, prefix: str) -> dict[str, object]:
    bundle, primary, manifest = build_resources()
    output.mkdir(parents=True, exist_ok=True)
    (output / "bundle.bin").write_bytes(words_to_bytes(bundle))
    (output / "primary.bin").write_bytes(words_to_bytes(primary))
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    write_c_output(output, prefix, bundle, primary)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--prefix", default="mobigo_clean_family_a")
    args = parser.parse_args()
    manifest = write_outputs(args.output, args.prefix)
    print(
        "PASS "
        f"bundle_words={manifest['bundle_word_count']} "
        f"primary_words={manifest['primary_word_count']} "
        f"output={args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
