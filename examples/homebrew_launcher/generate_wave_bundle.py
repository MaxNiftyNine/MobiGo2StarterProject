#!/usr/bin/env python3
"""Generate the launcher's simple full-screen fast wave background."""

from __future__ import annotations

import argparse
import hashlib
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


WIDTH = 320
HEIGHT = 240
CELL = 16
MAP_WORDS = 0x400
WAVE_WIDTH = 80
WAVE_HEIGHT = 16
WAVE_FRAMES = 4
WAVE_DURATION = 2
MODE_WAVE = 0


def background_canvas() -> Canvas:
    canvas = Canvas(WIDTH, HEIGHT)
    for y in range(HEIGHT):
        for x in range(WIDTH):
            band = 1 if 54 <= y < 59 or 111 <= y < 116 or 164 <= y < 169 else 0
            canvas.put(x, y, band)
    # Offset the quiet bands so the animated crests do not look like a grid.
    for x in range(WIDTH):
        for base, phase in ((55, 0.0), (112, 1.7), (165, 3.1)):
            crest = base + int(4 * math.sin(x / 25.0 + phase))
            for y in range(base - 5, base + 6):
                canvas.put(x, y, 1 if y >= crest else 0)
    return canvas


def wave_frame(frame: int) -> Canvas:
    canvas = Canvas(WAVE_WIDTH, WAVE_HEIGHT)
    phase = frame * (math.pi / 2.0)
    for x in range(WAVE_WIDTH):
        crest = 7 + int(4.5 * math.sin(x / 8.0 + phase))
        for thickness in range(3):
            canvas.put(x, min(WAVE_HEIGHT - 1, crest + thickness), 3)
    return canvas


def _append_image(primary: list[int], canvas: Canvas) -> int:
    offset = len(primary)
    primary.extend(bytes_to_words(pack_2bpp(canvas.pixels, canvas.width, canvas.height)))
    return offset


def build_resources() -> tuple[list[int], list[int], dict[str, object]]:
    background = background_canvas()
    waves = [wave_frame(index) for index in range(WAVE_FRAMES)]
    even = [rgb555(0, 0, 0)] * PALETTE_SOURCE_WORDS
    odd = [rgb555(0, 0, 0)] * PALETTE_SOURCE_WORDS
    even[:4] = [
        rgb555(8, 23, 31), rgb555(10, 26, 31),
        rgb555(23, 30, 31), rgb555(31, 31, 31),
    ]
    odd[:4] = [
        rgb555(0, 0, 0, transparent=True), rgb555(3, 8, 15),
        rgb555(29, 31, 31), rgb555(5, 22, 31),
    ]
    primary = even + odd

    tilemap_offset = len(primary)
    primary.extend([0] * MAP_WORDS)
    graphics_offset = len(primary)
    primary.extend([0] * (CELL * CELL // 8))
    tile_ids: dict[bytes, int] = {}
    tilemap = [0] * MAP_WORDS
    next_tile = 1
    for tile_y in range(HEIGHT // CELL):
        for tile_x in range(WIDTH // CELL):
            pixels = bytes(
                background.pixels[(tile_y * CELL + y) * WIDTH + tile_x * CELL + x]
                for y in range(CELL) for x in range(CELL)
            )
            packed = pack_2bpp(pixels, CELL, CELL)
            if packed not in tile_ids:
                tile_ids[packed] = next_tile
                primary.extend(bytes_to_words(packed))
                next_tile += 1
            tilemap[tile_y * (WIDTH // CELL) + tile_x] = tile_ids[packed]
    primary[tilemap_offset : tilemap_offset + MAP_WORDS] = tilemap
    wave_offsets = [_append_image(primary, frame) for frame in waves]

    graph = WordBuilder()
    graph.reserve(HEADER_WORDS)
    graph.label("lookup")
    lookup = graph.reserve(WAVE_FRAMES * 4)
    graph.label("ui_a_table")
    ui_a = graph.reserve(10)
    graph.label("ui_b_table")
    ui_b = graph.reserve(12)
    graph.label("auto_instances")
    graph.reserve(4)
    graph.label("background")
    background_image = graph.reserve(18)
    graph.label("background_slot")
    graph.add(0, 0)
    graph.label("modes")
    modes = graph.add(*u32_words(1), 0, 0)
    graph.label("records")
    records = graph.add(*u32_words(WAVE_FRAMES))
    graph.reserve(WAVE_FRAMES * 14)

    for index, primary_offset in enumerate(wave_offsets):
        component_label = f"wave_{index}_components"
        bitmap_label = f"wave_{index}_bitmap"
        slot_label = f"wave_{index}_slot"
        graph.label(component_label)
        component = graph.add(*u32_words(1), 0, 0, 0, 0)
        graph.label(bitmap_label)
        bitmap = graph.add(0, WAVE_WIDTH, WAVE_HEIGHT, 0, 0, 0)
        graph.label(slot_label)
        graph.add(0, 0)
        graph.set_relative(component + 4, bitmap_label)
        graph.set_u32(bitmap + 4, lookup + index * 4 - HEADER_WORDS)
        entry = lookup + index * 4
        graph.set_u16(entry, (WAVE_HEIGHT << 8) | WAVE_WIDTH)
        graph.set_u16(entry + 1, 0)
        graph.set_u32(entry + 2, PRIMARY_TAG + primary_offset)
        record = records + 2 + index * 14
        graph.words[record : record + 10] = [
            0, 0, WAVE_DURATION,
            signed_word(-(WAVE_WIDTH // 2)), WAVE_WIDTH // 2,
            signed_word(-(WAVE_HEIGHT // 2)), WAVE_HEIGHT // 2,
            0, 0xFFFF, 0xFFFF,
        ]
        graph.set_relative(record + 10, component_label)
        graph.set_relative(record + 12, slot_label)

    graph.set_u32(0x00, 0x80000002)
    graph.set_u32(0x02, PRIMARY_TAG)
    graph.set_u32(0x04, PRIMARY_TAG + PALETTE_SOURCE_WORDS)
    graph.set_u32(0x06, SECONDARY_TAG)
    graph.set_u32(0x08, SECONDARY_TAG + 0x100)
    graph.set_u16(0x0A, WAVE_FRAMES)
    graph.set_relative(0x0C, "lookup")
    graph.set_relative(0x10, "ui_a_table")
    graph.set_u16(0x12, 1)
    graph.set_relative(0x14, "ui_a_table")
    graph.set_u16(0x16, 1)
    graph.set_relative(0x18, "ui_b_table")
    graph.set_relative(0x1A, "auto_instances")
    graph.words[ui_a : ui_a + 10] = [1, 0, 0, 0, 0, 0x40, 0xFFFF, 0xFFFF, 0, 0]
    graph.set_relative(ui_a + 8, "background")
    graph.words[background_image : background_image + 18] = [
        WIDTH, HEIGHT, CELL, CELL, 0, 0, HEIGHT - 1, 0, WIDTH - 1,
        0, 0, 0, 0, 0, 0, 0, 0, 0,
    ]
    graph.set_u32(background_image + 10, PRIMARY_TAG + graphics_offset)
    graph.set_u32(background_image + 12, PRIMARY_TAG + tilemap_offset)
    graph.set_relative(background_image + 16, "background_slot")
    graph.words[ui_b : ui_b + 12] = [0, 0, 0, 0, 0, 0, 0, 0x40, 0xFFFF, 0xFFFF, 0, 0]
    graph.set_relative(ui_b + 10, "modes")
    graph.set_relative(modes + 2, "records")

    manifest = {
        "schema": 3,
        "provenance": "Original clean-room full-screen fast sine-wave artwork.",
        "bundle_word_count": len(graph.words),
        "primary_word_count": len(primary),
        "background_unique_tiles": len(tile_ids),
        "wave_frames": WAVE_FRAMES,
        "wave_duration": WAVE_DURATION,
        "primary_sha256": hashlib.sha256(words_to_bytes(primary)).hexdigest(),
    }
    return graph.words, primary, manifest


def write_outputs(output: Path, prefix: str) -> None:
    bundle, primary, manifest = build_resources()
    symbol = c_identifier(prefix)
    upper = symbol.upper()
    output.mkdir(parents=True, exist_ok=True)
    (output / "bundle.bin").write_bytes(words_to_bytes(bundle))
    (output / "primary.bin").write_bytes(words_to_bytes(primary))
    (output / "background.pgm").write_bytes(pgm_bytes(background_canvas()))
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (output / f"{prefix}_resources.h").write_text(f"""#ifndef {upper}_RESOURCES_H
#define {upper}_RESOURCES_H
#include "mobigo_sdk/mobigo_sdk.h"
enum {{ {upper}_BUNDLE_WORD_COUNT = {len(bundle)}, {upper}_MODE_WAVE = 0 }};
extern const unsigned short {symbol}_bundle_template[{len(bundle)}];
extern const unsigned short {symbol}_primary_words[{len(primary)}];
void {symbol}_copy_bundle(unsigned short *destination);
void {symbol}_register(unsigned short *writable_bundle);
mg_sdk_ui_handle {symbol}_create_background(void);
mg_sdk_ui_handle {symbol}_create_sprite(void);
#endif
""", encoding="ascii")
    (output / f"{prefix}_resources.c").write_text(f"""#include "{prefix}_resources.h"
const unsigned short {symbol}_bundle_template[{len(bundle)}] = {{
{c_words(bundle)}
}};
const unsigned short {symbol}_primary_words[{len(primary)}] = {{
{c_words(primary)}
}};
void {symbol}_copy_bundle(unsigned short *destination) {{
    unsigned short index;
    for (index = 0; index < {upper}_BUNDLE_WORD_COUNT; ++index)
        destination[index] = {symbol}_bundle_template[index];
}}
void {symbol}_register(unsigned short *writable_bundle) {{
    mg_sdk_resident_register_asset_bundle(
        writable_bundle, (void *){symbol}_primary_words, (void *)0);
}}
mg_sdk_ui_handle {symbol}_create_background(void) {{ return mg_sdk_ui_a_create(0); }}
mg_sdk_ui_handle {symbol}_create_sprite(void) {{ return mg_sdk_ui_b_create(0); }}
""", encoding="ascii")
    print(
        f"PASS launcher waves bundle_words={len(bundle)} primary_words={len(primary)} "
        f"tiles={manifest['background_unique_tiles']} duration={WAVE_DURATION} "
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
