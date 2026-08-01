#!/usr/bin/env python3
"""Build an original two-frame family-B animation bundle.

This is a compact reference generator for the recovered descriptor -> mode ->
record -> component -> bitmap -> chunk graph. It deliberately uses nonzero
record deltas and durations so the resident transition engine can be tested,
not merely the static sprite renderer.
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
    pgm_bytes,
    rgb555,
    signed_word,
    u32_words,
    words_to_bytes,
)


WIDTH = 16
HEIGHT = 16
FRAME_COUNT = 2


def draw_frame(index: int) -> Canvas:
    canvas = Canvas(WIDTH, HEIGHT)
    if index == 0:
        for y in range(4, 12):
            for x in range(2, 10):
                canvas.put(x, y, 2 if x < 8 else 3)
    else:
        for y in range(2, 14):
            half = 5 - abs(7 - y) // 2
            for x in range(8 - half, 9 + half):
                if 0 <= x < WIDTH:
                    canvas.put(x, y, 3 if (x + y) & 1 else 2)
    return canvas


def read_u32(words: list[int], offset: int) -> int:
    return words[offset] | (words[offset + 1] << 16)


def build_resources() -> tuple[list[int], list[int], dict[str, object], list[Canvas]]:
    frames = [draw_frame(0), draw_frame(1)]
    even_palette = [UNUSED_RGB555] * PALETTE_SOURCE_WORDS
    odd_palette = [UNUSED_RGB555] * PALETTE_SOURCE_WORDS
    odd_palette[:4] = [
        rgb555(0, 0, 0, transparent=True),
        rgb555(5, 9, 14),
        rgb555(31, 31, 31),
        rgb555(31, 12, 2),
    ]
    primary = even_palette + odd_palette
    primary_offsets: list[int] = []
    for frame in frames:
        primary_offsets.append(len(primary))
        primary.extend(bytes_to_words(pack_2bpp(frame.pixels, WIDTH, HEIGHT)))

    graph = WordBuilder()
    graph.reserve(HEADER_WORDS)
    graph.label("lookup")
    lookup = graph.reserve(FRAME_COUNT * 4)
    graph.label("empty")
    graph.label("ui_b_table")
    descriptor = graph.reserve(12)
    graph.label("auto_handles")
    graph.reserve(4)
    graph.label("modes")
    modes = graph.add(*u32_words(1), 0, 0)
    graph.label("records")
    records = graph.add(*u32_words(FRAME_COUNT))
    graph.reserve(FRAME_COUNT * 14)

    for index in range(FRAME_COUNT):
        component_label = f"frame_{index}_components"
        bitmap_label = f"frame_{index}_bitmap"
        slot_label = f"frame_{index}_slot"
        graph.label(component_label)
        component = graph.add(*u32_words(1), signed_word(-8), signed_word(-8), 0, 0)
        graph.label(bitmap_label)
        bitmap = graph.add(0, WIDTH, HEIGHT, 0, 0, 0)
        graph.label(slot_label)
        graph.add(0, 0)
        graph.set_relative(component + 4, bitmap_label)
        graph.set_u32(bitmap + 4, lookup + index * 4 - HEADER_WORDS)

        entry = lookup + index * 4
        graph.set_u16(entry, (HEIGHT << 8) | WIDTH)
        graph.set_u16(entry + 1, 0)
        graph.set_u32(entry + 2, PRIMARY_TAG + primary_offsets[index])

        record = records + 2 + index * 14
        # Retail animation modes commonly keep record zero stationary and put
        # the movement delta on the destination record.
        delta_x = 0 if index == 0 else 4
        graph.words[record : record + 10] = [
            signed_word(delta_x), 0, 20,
            signed_word(-8), 8, signed_word(-8), 8,
            0, 0xffff, 0xffff,
        ]
        graph.set_relative(record + 10, component_label)
        graph.set_relative(record + 12, slot_label)

    graph.set_u32(0x00, 0x80000002)
    graph.set_u32(0x02, PRIMARY_TAG)
    graph.set_u32(0x04, PRIMARY_TAG + PALETTE_SOURCE_WORDS)
    graph.set_u32(0x06, SECONDARY_TAG)
    graph.set_u32(0x08, SECONDARY_TAG + 0x100)
    graph.set_u16(0x0A, FRAME_COUNT)
    graph.set_relative(0x0C, "lookup")
    graph.set_relative(0x10, "empty")
    graph.set_u16(0x12, 0)
    graph.set_relative(0x14, "empty")
    graph.set_u16(0x16, 1)
    graph.set_relative(0x18, "ui_b_table")
    graph.set_relative(0x1A, "auto_handles")

    graph.words[descriptor : descriptor + 12] = [
        0, 80, 120, 0, 0, 0, 0, 0x40, 0xffff, 0xffff, 0, 0
    ]
    graph.set_relative(descriptor + 10, "modes")
    graph.set_relative(modes + 2, "records")

    if read_u32(graph.words, 0) != 0x80000002:
        raise ValueError("invalid bundle version")
    if graph.words[0x16] != 1 or graph.words[0x0A] != FRAME_COUNT:
        raise ValueError("invalid descriptor/lookup counts")
    manifest: dict[str, object] = {
        "schema": 1,
        "provenance": "Clean-room graph and original programmatic artwork; no retail asset bytes are consumed.",
        "bundle_word_count": len(graph.words),
        "primary_word_count": len(primary),
        "descriptor": 0,
        "mode": 0,
        "record_count": FRAME_COUNT,
        "record_delta_x": [0, 4],
        "record_duration": [20, 20],
        "frames": [
            {
                "index": index,
                "primary_word_offset": primary_offsets[index],
                "sha256": hashlib.sha256(
                    words_to_bytes(primary[primary_offsets[index] : primary_offsets[index] + 32])
                ).hexdigest(),
            }
            for index in range(FRAME_COUNT)
        ],
    }
    return graph.words, primary, manifest, frames


def write_outputs(output: Path, prefix: str) -> dict[str, object]:
    bundle, primary, manifest, frames = build_resources()
    symbol = c_identifier(prefix)
    guard = f"{symbol.upper()}_RESOURCES_H"
    output.mkdir(parents=True, exist_ok=True)
    previews = output / "previews"
    previews.mkdir(exist_ok=True)
    (output / "bundle.bin").write_bytes(words_to_bytes(bundle))
    (output / "primary.bin").write_bytes(words_to_bytes(primary))
    for index, frame in enumerate(frames):
        (previews / f"frame_{index}.pgm").write_bytes(pgm_bytes(frame))
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

    header = f"""#ifndef {guard}
#define {guard}
#include "mobigo_sdk/mobigo_sdk.h"
enum {{
    {symbol.upper()}_BUNDLE_WORD_COUNT = {len(bundle)},
    {symbol.upper()}_DESCRIPTOR = 0
}};
extern const unsigned short {symbol}_primary_words[{len(primary)}];
void {symbol}_copy_bundle(unsigned short *destination);
void {symbol}_register(unsigned short *writable_bundle);
mg_sdk_ui_handle {symbol}_create(void);
#endif
"""
    source = f"""#include "{symbol}_resources.h"
static const unsigned short {symbol}_bundle_template[{len(bundle)}] = {{
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
        writable_bundle, (void *){symbol}_primary_words, (void *)0);
}}
mg_sdk_ui_handle {symbol}_create(void)
{{
    return mg_sdk_ui_b_create({symbol.upper()}_DESCRIPTOR);
}}
"""
    (output / f"{symbol}_resources.h").write_text(header)
    (output / f"{symbol}_resources.c").write_text(source)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--prefix", default="mobigo_clean_animation")
    args = parser.parse_args()
    manifest = write_outputs(args.output, args.prefix)
    print(
        f"PASS animation bundle_words={manifest['bundle_word_count']} "
        f"primary_words={manifest['primary_word_count']} output={args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
