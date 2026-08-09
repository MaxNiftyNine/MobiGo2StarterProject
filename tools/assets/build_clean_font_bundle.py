#!/usr/bin/env python3
"""Build an original ASCII glyph bundle for the recovered MobiGo UI runtime.

The bundle mirrors only the structure recovered from EBOOK's ``ft01`` path: a
family-B descriptor whose record selector is the character code. All glyph
artwork below is clean-room, hand-authored 5x7 block art placed in transparent
16x16 2-bpp sprite cells. No retail font/resource bytes are read.
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

FONT_CELL_WIDTH = 16
FONT_CELL_HEIGHT = 16
FONT_GLYPH_WIDTH = 6
FONT_GLYPH_HEIGHT = 8
FONT_DURATION = 20
FONT_RECORD_COUNT = 128
FONT_DESCRIPTOR = 0
FONT_MODE = 0
FONT_ADVANCE = 6

# Original 5x7 patterns. '#' is foreground, '.' is transparent.
PATTERNS = {
    "?": [".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."],
    "!": ["..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."],
    ".": [".....", ".....", ".....", ".....", ".....", ".....", "..#.."],
    ",": [".....", ".....", ".....", ".....", ".....", "..#..", ".#..."],
    ":": [".....", "..#..", ".....", ".....", "..#..", ".....", "....."],
    "-": [".....", ".....", ".....", ".###.", ".....", ".....", "....."],
    "+": [".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."],
    "/": ["....#", "...#.", "...#.", "..#..", ".#...", ".#...", "#...."],
    "0": [".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."],
    "1": ["..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."],
    "2": [".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"],
    "3": ["####.", "....#", "....#", ".###.", "....#", "....#", "####."],
    "4": ["...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."],
    "5": ["#####", "#....", "#....", "####.", "....#", "....#", "####."],
    "6": [".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."],
    "7": ["#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."],
    "8": [".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."],
    "9": [".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."],
    "A": [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "B": ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."],
    "C": [".####", "#....", "#....", "#....", "#....", "#....", ".####"],
    "D": ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."],
    "E": ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    "F": ["#####", "#....", "#....", "####.", "#....", "#....", "#...."],
    "G": [".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."],
    "H": ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "I": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"],
    "J": ["..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."],
    "K": ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"],
    "L": ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
    "M": ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"],
    "N": ["#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"],
    "O": [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "P": ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."],
    "Q": [".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"],
    "R": ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
    "S": [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
    "T": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    "U": ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "V": ["#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."],
    "W": ["#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"],
    "X": ["#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"],
    "Y": ["#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."],
    "Z": ["#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"],
}


def glyph_key(code: int) -> str:
    if code == 0x20:
        return " "
    ch = chr(code) if 0 <= code < 128 else "?"
    if "a" <= ch <= "z":
        ch = ch.upper()
    return ch if ch in PATTERNS else "?"


def draw_glyph(key: str) -> Canvas:
    canvas = Canvas(FONT_CELL_WIDTH, FONT_CELL_HEIGHT)
    if key == " ":
        return canvas
    pattern = PATTERNS[key]
    for y, row in enumerate(pattern):
        if len(row) != 5:
            raise ValueError(f"{key}: row width is not five")
        for x, value in enumerate(row):
            if value == "#":
                canvas.put(x + 1, y, 2)
    return canvas


def add_family_b_descriptor(graph: WordBuilder, offset: int, nested_label: str) -> None:
    graph.words[offset : offset + 12] = [
        1, 0, 0, 0, 0, 0, 0, 0x0040, 0xFFFF, 0xFFFF, 0, 0
    ]
    graph.set_relative(offset + 10, nested_label)


def read_u32(words: list[int], offset: int) -> int:
    return words[offset] | (words[offset + 1] << 16)


def validate_bundle(
    bundle: list[int], primary: list[int], glyph_count: int, record_count: int
) -> None:
    if read_u32(bundle, 0) != 0x80000002:
        raise ValueError("font bundle is not version 2")
    if bundle[0x0A] != glyph_count:
        raise ValueError("font lookup count mismatch")
    if bundle[0x12] != 0 or bundle[0x16] != 1:
        raise ValueError("font family counts mismatch")
    descriptor = HEADER_WORDS + read_u32(bundle, 0x18)
    modes = HEADER_WORDS + read_u32(bundle, descriptor + 10)
    if read_u32(bundle, modes) != 1:
        raise ValueError("font descriptor must expose exactly one mode")
    records = HEADER_WORDS + read_u32(bundle, modes + 2)
    if read_u32(bundle, records) != record_count:
        raise ValueError("font record count mismatch")
    if len(primary) < PALETTE_SOURCE_WORDS * 2:
        raise ValueError("font primary image is missing palette windows")
    for code in range(record_count):
        record = records + 2 + code * 14
        component = HEADER_WORDS + read_u32(bundle, record + 10)
        slot = HEADER_WORDS + read_u32(bundle, record + 12)
        if read_u32(bundle, component) != 1:
            raise ValueError(f"font record {code} has invalid component count")
        if bundle[slot] != 0 or bundle[slot + 1] != 0:
            raise ValueError(f"font record {code} runtime slot is not clear")


def build_resources(
    record_count: int = FONT_RECORD_COUNT,
) -> tuple[list[int], list[int], dict[str, object], dict[str, Canvas]]:
    if record_count < 64 or record_count > FONT_RECORD_COUNT:
        raise ValueError("record_count must be in range 64..128")
    glyphs = {key: draw_glyph(key) for key in [" ", *sorted(PATTERNS)]}

    # Dynamic slots do not reload the global hardware palette. These palette
    # words remain structurally valid; the clean demo registers system UI in
    # slot 0 first and reuses its selector-0 sprite palette.
    even_palette = [UNUSED_RGB555] * PALETTE_SOURCE_WORDS
    odd_palette = [UNUSED_RGB555] * PALETTE_SOURCE_WORDS
    odd_palette[:4] = [
        rgb555(0, 0, 0, transparent=True),
        rgb555(4, 7, 12),
        rgb555(31, 31, 31),
        rgb555(31, 18, 3),
    ]
    primary = even_palette + odd_palette

    image_offsets: dict[str, int] = {}
    for key, canvas in glyphs.items():
        image_offsets[key] = len(primary)
        primary.extend(
            bytes_to_words(
                pack_2bpp(canvas.pixels, FONT_CELL_WIDTH, FONT_CELL_HEIGHT)
            )
        )

    graph = WordBuilder()
    graph.reserve(HEADER_WORDS)
    graph.label("lookup")
    lookup_offset = graph.reserve(len(glyphs) * 4)
    graph.label("aux_and_ui_a_empty")
    graph.label("ui_b_table")
    descriptor_offset = graph.reserve(12)
    graph.label("auto_instance_table")
    graph.reserve(4)
    graph.label("font_modes")
    mode_root = graph.add(*u32_words(1), 0, 0)
    graph.label("font_records")
    records = graph.add(*u32_words(record_count))
    graph.reserve(record_count * 14)

    component_labels: dict[str, str] = {}
    for index, (key, canvas) in enumerate(glyphs.items()):
        safe = "space" if key == " " else f"u{ord(key):04x}"
        component = f"glyph_{safe}_components"
        bitmap = f"glyph_{safe}_bitmap"
        component_labels[key] = component
        graph.label(component)
        component_offset = graph.add(*u32_words(1), 0, 0, 0, 0)
        graph.label(bitmap)
        bitmap_offset = graph.add(
            0, FONT_CELL_WIDTH, FONT_CELL_HEIGHT, 0, 0, 0
        )
        graph.set_relative(component_offset + 4, bitmap)
        lookup_entry = lookup_offset + index * 4
        graph.set_u32(bitmap_offset + 4, lookup_entry - HEADER_WORDS)
        graph.set_u16(
            lookup_entry,
            (FONT_CELL_HEIGHT << 8) | FONT_CELL_WIDTH,
        )
        graph.set_u16(lookup_entry + 1, 0)
        graph.set_u32(lookup_entry + 2, PRIMARY_TAG + image_offsets[key])

    runtime_labels: list[str] = []
    for code in range(record_count):
        label = f"glyph_record_{code:03d}_slot"
        runtime_labels.append(label)
        graph.label(label)
        graph.add(0, 0)

    graph.set_u32(0x00, 0x80000002)
    graph.set_u32(0x02, PRIMARY_TAG)
    graph.set_u32(0x04, PRIMARY_TAG + PALETTE_SOURCE_WORDS)
    graph.set_u32(0x06, SECONDARY_TAG)
    graph.set_u32(0x08, SECONDARY_TAG + 0x100)
    graph.set_u16(0x0A, len(glyphs))
    graph.set_relative(0x0C, "lookup")
    graph.set_relative(0x10, "aux_and_ui_a_empty")
    graph.set_u16(0x12, 0)
    graph.set_relative(0x14, "aux_and_ui_a_empty")
    graph.set_u16(0x16, 1)
    graph.set_relative(0x18, "ui_b_table")
    graph.set_relative(0x1A, "auto_instance_table")

    add_family_b_descriptor(graph, descriptor_offset, "font_modes")
    graph.set_relative(mode_root + 2, "font_records")

    for code in range(record_count):
        key = glyph_key(code)
        offset = records + 2 + code * 14
        graph.words[offset : offset + 10] = [
            0, 0, FONT_DURATION, signed_word(0), FONT_GLYPH_HEIGHT,
            signed_word(0),
            FONT_ADVANCE, 0, 0xFFFF, 0xFFFF,
        ]
        graph.set_relative(offset + 10, component_labels[key])
        graph.set_relative(offset + 12, runtime_labels[code])

    validate_bundle(graph.words, primary, len(glyphs), record_count)
    manifest: dict[str, object] = {
        "schema": 1,
        "provenance": "Clean-room graph and original 5x7 glyph artwork; no retail font bytes are consumed.",
        "bundle_version": "0x80000002",
        "bundle_word_count": len(graph.words),
        "primary_word_count": len(primary),
        "descriptor": FONT_DESCRIPTOR,
        "mode": FONT_MODE,
        "record_count": record_count,
        "cell_width": FONT_CELL_WIDTH,
        "cell_height": FONT_CELL_HEIGHT,
        "glyph_width": FONT_GLYPH_WIDTH,
        "glyph_height": FONT_GLYPH_HEIGHT,
        "record_duration": FONT_DURATION,
        "advance": FONT_ADVANCE,
        "supported_artwork": sorted(glyphs),
        "lowercase_maps_to_uppercase": True,
        "glyphs": {
            key: {
                "primary_word_offset": f"{image_offsets[key]:#06x}",
                "sha256": hashlib.sha256(
                    words_to_bytes(
                        primary[
                            image_offsets[key] :
                            image_offsets[key]
                            + FONT_CELL_WIDTH * FONT_CELL_HEIGHT // 8
                        ]
                    )
                ).hexdigest(),
            }
            for key in glyphs
        },
        "labels": {
            name: f"{offset:#06x}"
            for name, offset in sorted(graph.labels.items(), key=lambda item: item[1])
        },
    }
    return graph.words, primary, manifest, glyphs


def write_c_output(
    output: Path,
    prefix: str,
    bundle: list[int],
    primary: list[int],
    record_count: int,
) -> None:
    symbol = c_identifier(prefix)
    upper = symbol.upper()
    guard = f"{upper}_RESOURCES_H"
    header = f"""#ifndef {guard}
#define {guard}

#include "mobigo_sdk/resident_resources.h"

enum {{
    {upper}_DESCRIPTOR = {FONT_DESCRIPTOR},
    {upper}_MODE = {FONT_MODE},
    {upper}_RECORD_COUNT = {record_count},
    {upper}_CELL_WIDTH = {FONT_CELL_WIDTH},
    {upper}_CELL_HEIGHT = {FONT_CELL_HEIGHT},
    {upper}_GLYPH_WIDTH = {FONT_GLYPH_WIDTH},
    {upper}_GLYPH_HEIGHT = {FONT_GLYPH_HEIGHT},
    {upper}_RECORD_DURATION = {FONT_DURATION},
    {upper}_ADVANCE = {FONT_ADVANCE},
    {upper}_BUNDLE_WORD_COUNT = {len(bundle)},
    {upper}_PRIMARY_WORD_COUNT = {len(primary)}
}};

extern const unsigned short {symbol}_bundle_template[{len(bundle)}];
extern const unsigned short {symbol}_primary_words[{len(primary)}];

void {symbol}_copy_bundle(unsigned short *destination);
mg_sdk_u16 {symbol}_register_dynamic(unsigned short *writable_bundle);
mg_sdk_ui_handle {symbol}_create_glyph(
    mg_sdk_u16 slot, mg_sdk_u16 character, mg_sdk_u16 x, mg_sdk_u16 y);
void {symbol}_destroy_glyph(mg_sdk_ui_handle handle);

/*
 * Draw a NUL-terminated ASCII string using resident family-B anchor
 * coordinates. Spaces advance without consuming an object. Returns the
 * number of created glyph objects, or 0xffff after destroying any partial
 * run when capacity/object allocation is insufficient.
 */
mg_sdk_u16 {symbol}_create_text(
    mg_sdk_u16 slot,
    const char *text,
    mg_sdk_u16 anchor_x,
    mg_sdk_u16 anchor_y,
    mg_sdk_ui_handle *handles,
    mg_sdk_u16 handle_capacity);
void {symbol}_destroy_text(
    mg_sdk_ui_handle *handles,
    mg_sdk_u16 handle_count);

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
    for (index = 0; index < {upper}_BUNDLE_WORD_COUNT; ++index) {{
        destination[index] = {symbol}_bundle_template[index];
    }}
}}

mg_sdk_u16 {symbol}_register_dynamic(unsigned short *writable_bundle)
{{
    return mg_sdk_resident_register_dynamic_bundle(
        writable_bundle, (void *){symbol}_primary_words);
}}

mg_sdk_ui_handle {symbol}_create_glyph(
    mg_sdk_u16 slot, mg_sdk_u16 character, mg_sdk_u16 x, mg_sdk_u16 y)
{{
    mg_sdk_ui_handle handle;
    unsigned short *object;
    if (character >= (mg_sdk_u16)'a' && character <= (mg_sdk_u16)'z') {{
        character = (mg_sdk_u16)(character - 32U);
    }}
    if (character >= {upper}_RECORD_COUNT) {{
        character = (mg_sdk_u16)'?';
    }}
    handle = mg_sdk_ui_b_create_from_dynamic_bundle(slot, {upper}_DESCRIPTOR);
    if (handle == MG_SDK_INVALID_UI_HANDLE) {{
        return handle;
    }}
    object = (unsigned short *)mg_sdk_ui_b_get(handle);
    if (object == (unsigned short *)0) {{
        mg_sdk_ui_b_destroy(handle);
        return MG_SDK_INVALID_UI_HANDLE;
    }}
    object[0] = 1;
    object[1] = x;
    object[2] = y;
    object[3] = 0;
    object[5] = {upper}_MODE;
    object[6] = character;
    object[7] = 1;
    return handle;
}}

void {symbol}_destroy_glyph(mg_sdk_ui_handle handle)
{{
    if (handle != MG_SDK_INVALID_UI_HANDLE) {{
        mg_sdk_ui_b_destroy(handle);
    }}
}}

mg_sdk_u16 {symbol}_create_text(
    mg_sdk_u16 slot,
    const char *text,
    mg_sdk_u16 anchor_x,
    mg_sdk_u16 anchor_y,
    mg_sdk_ui_handle *handles,
    mg_sdk_u16 handle_capacity)
{{
    mg_sdk_u16 count;
    mg_sdk_u16 character;
    mg_sdk_ui_handle handle;

    if (text == (const char *)0 ||
        (handles == (mg_sdk_ui_handle *)0 && handle_capacity != 0)) {{
        return 0xffff;
    }}

    count = 0;
    while (*text != 0) {{
        character = (mg_sdk_u16)*text & 0x00ff;
        if (character != (mg_sdk_u16)' ') {{
            if (count >= handle_capacity) {{
                {symbol}_destroy_text(handles, count);
                return 0xffff;
            }}
            handle = {symbol}_create_glyph(
                slot, character, anchor_x, anchor_y);
            if (handle == MG_SDK_INVALID_UI_HANDLE) {{
                {symbol}_destroy_text(handles, count);
                return 0xffff;
            }}
            handles[count] = handle;
            ++count;
        }}
        anchor_x = (mg_sdk_u16)(anchor_x + {upper}_ADVANCE);
        ++text;
    }}
    return count;
}}

void {symbol}_destroy_text(
    mg_sdk_ui_handle *handles,
    mg_sdk_u16 handle_count)
{{
    mg_sdk_u16 index;
    if (handles == (mg_sdk_ui_handle *)0) {{
        return;
    }}
    for (index = 0; index < handle_count; ++index) {{
        {symbol}_destroy_glyph(handles[index]);
        handles[index] = MG_SDK_INVALID_UI_HANDLE;
    }}
}}
"""
    (output / f"{prefix}_resources.h").write_text(header)
    (output / f"{prefix}_resources.c").write_text(source)


def write_outputs(
    output: Path, prefix: str, record_count: int = FONT_RECORD_COUNT
) -> dict[str, object]:
    bundle, primary, manifest, glyphs = build_resources(record_count)
    output.mkdir(parents=True, exist_ok=True)
    previews = output / "previews"
    previews.mkdir(exist_ok=True)
    (output / "bundle.bin").write_bytes(words_to_bytes(bundle))
    (output / "primary.bin").write_bytes(words_to_bytes(primary))
    for key, canvas in glyphs.items():
        safe = "space" if key == " " else f"u{ord(key):04x}"
        (previews / f"{safe}.pgm").write_bytes(pgm_bytes(canvas))
    write_c_output(output, prefix, bundle, primary, record_count)
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--prefix", default="mobigo_clean_font")
    parser.add_argument(
        "--record-count",
        type=int,
        default=FONT_RECORD_COUNT,
        help="record table size (64..128); 96 covers printable ASCII",
    )
    args = parser.parse_args()
    manifest = write_outputs(args.output, args.prefix, args.record_count)
    print(
        f"PASS font bundle_words={manifest['bundle_word_count']} "
        f"primary_words={manifest['primary_word_count']} output={args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
