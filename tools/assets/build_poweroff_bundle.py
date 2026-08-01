#!/usr/bin/env python3
"""Build an original MobiGo-compatible family-B power-off overlay bundle.

G1 and SY independently use the same graph shape for the off presentation:
one family-B mode, one 14-word record, one component, and a 176x32 2-bpp
bitmap split into 64+64+32+16 pixel chunks.  This tool reproduces that
structure with newly drawn artwork only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from build_standard_settings_bundle import (
    HEADER_WORDS,
    PALETTE_SOURCE_WORDS,
    PRIMARY_TAG,
    SECONDARY_TAG,
    UNUSED_RGB555,
    Canvas,
    WordBuilder,
    bytes_to_words,
    c_identifier,
    c_words,
    pack_2bpp,
    rgb555,
    signed_word,
    u32_words,
    words_to_bytes,
)

WIDTH = 176
HEIGHT = 32
CHUNK_WIDTHS = (64, 64, 32, 16)


def draw_poweroff() -> Canvas:
    canvas = Canvas(WIDTH, HEIGHT)

    # Original power symbol.
    canvas.circle(18, 16, 11, 2)
    canvas.rect(16, 2, 20, 16, 3)
    canvas.rect(17, 4, 19, 15, 2)

    # A compact original "OFF" wordmark, drawn from rectangles.
    x = 43
    canvas.rect(x, 8, x + 4, 25, 3)
    canvas.rect(x, 8, x + 16, 12, 3)
    canvas.rect(x, 21, x + 16, 25, 3)
    canvas.rect(x + 12, 8, x + 16, 25, 3)

    x = 67
    canvas.rect(x, 8, x + 4, 25, 3)
    canvas.rect(x, 8, x + 17, 12, 3)
    canvas.rect(x, 15, x + 14, 19, 3)

    x = 91
    canvas.rect(x, 8, x + 4, 25, 3)
    canvas.rect(x, 8, x + 17, 12, 3)
    canvas.rect(x, 15, x + 14, 19, 3)

    # Progress/accent marks make the 176-pixel geometry visually obvious.
    for index in range(6):
        x0 = 124 + index * 7
        canvas.rect(x0, 13, x0 + 4, 20, 1 if index < 4 else 2)
    return canvas


def slice_canvas(canvas: Canvas, x0: int, width: int) -> Canvas:
    result = Canvas(width, canvas.height)
    for y in range(canvas.height):
        for x in range(width):
            result.put(x, y, canvas.pixels[y * canvas.width + x0 + x])
    return result


def build_resources() -> tuple[list[int], list[int], dict[str, object], Canvas]:
    canvas = draw_poweroff()
    even_palette = [UNUSED_RGB555] * PALETTE_SOURCE_WORDS
    odd_palette = [UNUSED_RGB555] * PALETTE_SOURCE_WORDS
    odd_palette[:4] = [
        rgb555(0, 0, 0, transparent=True),
        rgb555(4, 7, 12),
        rgb555(31, 31, 31),
        rgb555(31, 18, 3),
    ]
    primary = even_palette + odd_palette

    chunk_offsets: list[int] = []
    x = 0
    for width in CHUNK_WIDTHS:
        chunk = slice_canvas(canvas, x, width)
        chunk_offsets.append(len(primary))
        primary.extend(bytes_to_words(pack_2bpp(chunk.pixels, width, HEIGHT)))
        x += width
    if x != WIDTH:
        raise ValueError("power-off chunk widths do not cover the bitmap")

    graph = WordBuilder()
    graph.reserve(HEADER_WORDS)
    graph.label("lookup")
    lookup_offset = graph.reserve(len(CHUNK_WIDTHS) * 4)
    graph.label("aux_and_ui_a_empty")
    graph.label("ui_b_table")
    descriptor_offset = graph.reserve(12)
    graph.label("auto_instance_table")
    graph.label("generated_handles")
    graph.reserve(4)
    graph.label("poweroff_modes")
    root_offset = graph.add(*u32_words(1), 0, 0)
    graph.label("poweroff_record")
    mode_offset = graph.add(*u32_words(1))
    record_offset = graph.reserve(14)
    graph.label("poweroff_components")
    component_offset = graph.add(*u32_words(1), 0, 0, 0, 0)
    graph.label("poweroff_bitmap")
    bitmap_offset = graph.add(0, WIDTH, HEIGHT, 0, 0, 0)
    graph.label("poweroff_runtime_slot")
    graph.add(0, 0)

    graph.set_u32(0x00, 0x80000002)
    graph.set_u32(0x02, PRIMARY_TAG)
    graph.set_u32(0x04, PRIMARY_TAG + PALETTE_SOURCE_WORDS)
    graph.set_u32(0x06, SECONDARY_TAG)
    graph.set_u32(0x08, SECONDARY_TAG + 0x100)
    graph.set_u16(0x0A, len(CHUNK_WIDTHS))
    graph.set_relative(0x0C, "lookup")
    graph.set_relative(0x10, "aux_and_ui_a_empty")
    graph.set_u16(0x12, 0)
    graph.set_relative(0x14, "aux_and_ui_a_empty")
    graph.set_u16(0x16, 1)
    graph.set_relative(0x18, "ui_b_table")
    graph.set_relative(0x1A, "generated_handles")

    graph.words[descriptor_offset : descriptor_offset + 12] = [
        1, 0, 0, 0, 0, 0, 0, 0x40, 0xFFFF, 0xFFFF, 0, 0
    ]
    graph.set_relative(descriptor_offset + 10, "poweroff_modes")
    graph.set_relative(root_offset + 2, "poweroff_record")

    graph.words[record_offset : record_offset + 10] = [
        0,
        0,
        0x0014,
        signed_word(-16),
        0x0010,
        signed_word(-88),
        0x0058,
        0,
        0xFFFF,
        0xFFFF,
    ]
    graph.set_relative(record_offset + 10, "poweroff_components")
    graph.set_relative(record_offset + 12, "poweroff_runtime_slot")

    graph.set_relative(component_offset + 4, "poweroff_bitmap")
    graph.set_u32(bitmap_offset + 4, graph.relative("lookup"))

    for index, (width, primary_offset) in enumerate(zip(CHUNK_WIDTHS, chunk_offsets)):
        entry = lookup_offset + index * 4
        graph.set_u16(entry, (HEIGHT << 8) | width)
        graph.set_u16(entry + 1, 0)
        graph.set_u32(entry + 2, PRIMARY_TAG + primary_offset)

    manifest: dict[str, object] = {
        "schema": 1,
        "provenance": "Clean-room graph and original programmatic artwork.",
        "address_unit": "16-bit words",
        "bundle_version": "0x80000002",
        "bundle_word_count": len(graph.words),
        "primary_word_count": len(primary),
        "ui_family_b_descriptor": 0,
        "mode": 0,
        "record": 0,
        "bitmap": {
            "width": WIDTH,
            "height": HEIGHT,
            "format_word": "0x0000",
            "chunk_widths": list(CHUNK_WIDTHS),
            "chunk_primary_word_offsets": [f"{offset:#06x}" for offset in chunk_offsets],
            "packed_sha256": hashlib.sha256(
                b"".join(
                    words_to_bytes(primary[offset : offset + width * HEIGHT // 8])
                    for offset, width in zip(chunk_offsets, CHUNK_WIDTHS)
                )
            ).hexdigest(),
        },
        "labels": {
            name: f"{offset:#06x}"
            for name, offset in sorted(graph.labels.items(), key=lambda item: item[1])
        },
    }
    return graph.words, primary, manifest, canvas


def pgm_bytes(canvas: Canvas) -> bytes:
    samples = bytes((0, 85, 170, 255)[value] for value in canvas.pixels)
    return f"P5\n{canvas.width} {canvas.height}\n255\n".encode() + samples


def write_c_output(output: Path, prefix: str, bundle: list[int], primary: list[int]) -> None:
    symbol = c_identifier(prefix)
    guard = f"{symbol.upper()}_POWEROFF_RESOURCES_H"
    header = f"""#ifndef {guard}
#define {guard}

#include "mobigo_sdk/resident_resources.h"

enum {{
    {symbol.upper()}_POWEROFF_DESCRIPTOR = 0,
    {symbol.upper()}_POWEROFF_MODE = 0,
    {symbol.upper()}_POWEROFF_RECORD = 0,
    {symbol.upper()}_BUNDLE_WORD_COUNT = {len(bundle)},
    {symbol.upper()}_PRIMARY_WORD_COUNT = {len(primary)}
}};

extern const unsigned short {symbol}_bundle_template[{len(bundle)}];
extern const unsigned short {symbol}_primary_words[{len(primary)}];

void {symbol}_copy_bundle(unsigned short *destination);
void {symbol}_register(unsigned short *writable_bundle);
mg_sdk_ui_handle {symbol}_create(void);

#endif
"""
    source = f"""#include "{prefix}_resources.h"

const unsigned short {symbol}_bundle_template[{len(bundle)}] = {{
{c_words(bundle)}
}};

const unsigned short {symbol}_primary_words[{len(primary)}] = {{
{c_words(primary)}
}};

void {symbol}_copy_bundle(unsigned short *destination)
{{
    unsigned short index;
    for (index = 0; index < {symbol.upper()}_BUNDLE_WORD_COUNT; ++index) {{
        destination[index] = {symbol}_bundle_template[index];
    }}
}}

void {symbol}_register(unsigned short *writable_bundle)
{{
    mg_sdk_resident_register_asset_bundle(
        writable_bundle,
        (void *){symbol}_primary_words,
        (void *)0);
}}

mg_sdk_ui_handle {symbol}_create(void)
{{
    return mg_sdk_ui_b_create({symbol.upper()}_POWEROFF_DESCRIPTOR);
}}
"""
    (output / f"{prefix}_resources.h").write_text(header)
    (output / f"{prefix}_resources.c").write_text(source)


def write_outputs(output: Path, prefix: str) -> dict[str, object]:
    bundle, primary, manifest, canvas = build_resources()
    output.mkdir(parents=True, exist_ok=True)
    (output / "bundle.bin").write_bytes(words_to_bytes(bundle))
    (output / "primary.bin").write_bytes(words_to_bytes(primary))
    (output / "poweroff.pgm").write_bytes(pgm_bytes(canvas))
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    write_c_output(output, prefix, bundle, primary)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--prefix", default="mobigo_clean_poweroff")
    args = parser.parse_args()
    manifest = write_outputs(args.output, args.prefix)
    print(
        f"PASS bundle_words={manifest['bundle_word_count']} "
        f"primary_words={manifest['primary_word_count']} "
        f"output={args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
