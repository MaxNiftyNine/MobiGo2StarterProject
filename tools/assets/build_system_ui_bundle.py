#!/usr/bin/env python3
"""Build one clean-room bundle for the shared MobiGo system UI.

The bundle combines the resident-compatible resources already validated
individually through the emulator:

* family-B descriptor 0: brightness (4 records) + volume (10 records)
* family-B descriptor 1: centered power-off presentation (1 record)

All artwork is generated programmatically.  No retail bitmap/palette payload is
read or copied.  The emitted C uses a const linked-bundle template plus an
explicit copy into caller-provided writable RAM because resident registration
rebases the graph in place.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from build_poweroff_bundle import CHUNK_WIDTHS, HEIGHT as POWEROFF_HEIGHT, draw_poweroff, slice_canvas
from build_standard_settings_bundle import (
    BITMAP_HEIGHT,
    BITMAP_WIDTH,
    BITMAP_WORDS,
    BRIGHTNESS_LEVELS,
    HEADER_WORDS,
    PALETTE_SOURCE_WORDS,
    PRIMARY_TAG,
    SECONDARY_TAG,
    UNUSED_RGB555,
    VOLUME_LEVELS,
    ImageResource,
    WordBuilder,
    bytes_to_words,
    c_identifier,
    c_words,
    draw_brightness,
    draw_volume,
    pack_2bpp,
    rgb555,
    signed_word,
    u32_words,
    words_to_bytes,
)

POWEROFF_WIDTH = sum(CHUNK_WIDTHS)
SETTINGS_DESCRIPTOR = 0
POWEROFF_DESCRIPTOR = 1
BRIGHTNESS_MODE = 0
VOLUME_MODE = 1
POWEROFF_MODE = 0
POWEROFF_RECORD = 0
BRIGHTNESS_X = 138
VOLUME_X = 109
SETTINGS_Y = 214

# Recovered system-controls policy and UI placement must agree.  These were
# once accidentally swapped in the generated adapter, so keep the invariant
# explicit beside the generator rather than relying only on visual tests.
assert BRIGHTNESS_X == 138
assert VOLUME_X == 109
assert BRIGHTNESS_X != VOLUME_X


def add_setting_record(
    graph: WordBuilder,
    record_offset: int,
    image: ImageResource,
    extent: int,
) -> None:
    graph.words[record_offset : record_offset + 10] = [
        0,
        0,
        0x0014,
        signed_word(-16),
        0x0010,
        signed_word(-36),
        extent,
        0,
        0xFFFF,
        0xFFFF,
    ]
    graph.set_relative(record_offset + 10, image.component_label)
    graph.set_relative(record_offset + 12, image.slot_label)


def add_family_b_descriptor(graph: WordBuilder, offset: int, nested_label: str) -> None:
    graph.words[offset : offset + 12] = [
        1, 0, 0, 0, 0, 0, 0, 0x0040, 0xFFFF, 0xFFFF, 0, 0
    ]
    graph.set_relative(offset + 10, nested_label)


def build_resources() -> tuple[list[int], list[int], dict[str, object]]:
    settings_images = [
        ImageResource(f"brightness_{level}", draw_brightness(level))
        for level in range(BRIGHTNESS_LEVELS)
    ]
    settings_images.extend(
        ImageResource(f"volume_{level}", draw_volume(level))
        for level in range(VOLUME_LEVELS)
    )
    poweroff_canvas = draw_poweroff()

    even_palette = [UNUSED_RGB555] * PALETTE_SOURCE_WORDS
    odd_palette = [UNUSED_RGB555] * PALETTE_SOURCE_WORDS
    odd_palette[:4] = [
        rgb555(0, 0, 0, transparent=True),
        rgb555(4, 7, 12),
        rgb555(31, 31, 31),
        rgb555(31, 18, 3),
    ]
    primary = even_palette + odd_palette

    for image in settings_images:
        image.primary_word_offset = len(primary)
        primary.extend(
            bytes_to_words(
                pack_2bpp(image.canvas.pixels, image.canvas.width, image.canvas.height)
            )
        )

    poweroff_chunk_primary_offsets: list[int] = []
    x = 0
    for width in CHUNK_WIDTHS:
        chunk = slice_canvas(poweroff_canvas, x, width)
        poweroff_chunk_primary_offsets.append(len(primary))
        primary.extend(bytes_to_words(pack_2bpp(chunk.pixels, width, POWEROFF_HEIGHT)))
        x += width
    if x != POWEROFF_WIDTH:
        raise ValueError("power-off chunks do not cover the full bitmap")

    graph = WordBuilder()
    graph.reserve(HEADER_WORDS)

    # Chunk lookup table: 14 one-chunk settings images + four off chunks.
    graph.label("lookup")
    lookup_offset = graph.reserve((len(settings_images) + len(CHUNK_WIDTHS)) * 4)

    graph.label("aux_and_ui_a_empty")
    graph.label("ui_b_table")
    settings_descriptor_offset = graph.reserve(12)
    poweroff_descriptor_offset = graph.reserve(12)

    # 0x1a table: two 32-bit markers followed by two 32-bit output handles.
    graph.label("auto_instance_table")
    graph.label("auto_instance_markers")
    graph.reserve(4)
    graph.label("auto_instance_handles")
    graph.reserve(4)

    graph.label("settings_modes")
    settings_root_offset = graph.add(*u32_words(2), 0, 0, 0, 0)
    graph.label("brightness_records")
    brightness_offset = graph.add(*u32_words(BRIGHTNESS_LEVELS))
    graph.reserve(BRIGHTNESS_LEVELS * 14)
    graph.label("volume_records")
    volume_offset = graph.add(*u32_words(VOLUME_LEVELS))
    graph.reserve(VOLUME_LEVELS * 14)

    graph.label("poweroff_modes")
    poweroff_root_offset = graph.add(*u32_words(1), 0, 0)
    graph.label("poweroff_records")
    poweroff_mode_offset = graph.add(*u32_words(1))
    poweroff_record_offset = graph.reserve(14)

    for index, image in enumerate(settings_images):
        image.lookup_word_offset = lookup_offset + index * 4
        image.component_label = f"{image.name}_components"
        image.bitmap_label = f"{image.name}_bitmap"
        image.slot_label = f"{image.name}_runtime_slot"

        graph.label(image.component_label)
        component_offset = graph.add(*u32_words(1), 0, 0, 0, 0)
        graph.label(image.bitmap_label)
        bitmap_offset = graph.add(0, BITMAP_WIDTH, BITMAP_HEIGHT, 0, 0, 0)
        graph.label(image.slot_label)
        graph.add(0, 0)

        graph.set_relative(component_offset + 4, image.bitmap_label)
        graph.set_u32(bitmap_offset + 4, image.lookup_word_offset - HEADER_WORDS)

        entry = image.lookup_word_offset
        graph.set_u16(entry, (BITMAP_HEIGHT << 8) | BITMAP_WIDTH)
        graph.set_u16(entry + 1, 0)
        graph.set_u32(entry + 2, PRIMARY_TAG + image.primary_word_offset)

    graph.label("poweroff_components")
    poweroff_component_offset = graph.add(*u32_words(1), 0, 0, 0, 0)
    graph.label("poweroff_bitmap")
    poweroff_bitmap_offset = graph.add(0, POWEROFF_WIDTH, POWEROFF_HEIGHT, 0, 0, 0)
    graph.label("poweroff_runtime_slot")
    graph.add(0, 0)
    graph.set_relative(poweroff_component_offset + 4, "poweroff_bitmap")
    poweroff_lookup_offset = lookup_offset + len(settings_images) * 4
    graph.set_u32(poweroff_bitmap_offset + 4, poweroff_lookup_offset - HEADER_WORDS)

    for index, (width, primary_offset) in enumerate(
        zip(CHUNK_WIDTHS, poweroff_chunk_primary_offsets)
    ):
        entry = poweroff_lookup_offset + index * 4
        graph.set_u16(entry, (POWEROFF_HEIGHT << 8) | width)
        graph.set_u16(entry + 1, 0)
        graph.set_u32(entry + 2, PRIMARY_TAG + primary_offset)

    graph.set_u32(0x00, 0x80000002)
    graph.set_u32(0x02, PRIMARY_TAG)
    graph.set_u32(0x04, PRIMARY_TAG + PALETTE_SOURCE_WORDS)
    graph.set_u32(0x06, SECONDARY_TAG)
    graph.set_u32(0x08, SECONDARY_TAG + 0x100)
    graph.set_u16(0x0A, len(settings_images) + len(CHUNK_WIDTHS))
    graph.set_relative(0x0C, "lookup")
    graph.set_relative(0x10, "aux_and_ui_a_empty")
    graph.set_u16(0x12, 0)
    graph.set_relative(0x14, "aux_and_ui_a_empty")
    graph.set_u16(0x16, 2)
    graph.set_relative(0x18, "ui_b_table")
    graph.set_relative(0x1A, "auto_instance_table")

    add_family_b_descriptor(graph, settings_descriptor_offset, "settings_modes")
    add_family_b_descriptor(graph, poweroff_descriptor_offset, "poweroff_modes")

    graph.set_relative(settings_root_offset + 2, "brightness_records")
    graph.set_relative(settings_root_offset + 4, "volume_records")
    for level, image in enumerate(settings_images[:BRIGHTNESS_LEVELS]):
        add_setting_record(graph, brightness_offset + 2 + level * 14, image, 0x002C)
    for level, image in enumerate(settings_images[BRIGHTNESS_LEVELS:]):
        add_setting_record(graph, volume_offset + 2 + level * 14, image, 0x006B)

    graph.set_relative(poweroff_root_offset + 2, "poweroff_records")
    graph.words[poweroff_record_offset : poweroff_record_offset + 10] = [
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
    graph.set_relative(poweroff_record_offset + 10, "poweroff_components")
    graph.set_relative(poweroff_record_offset + 12, "poweroff_runtime_slot")

    manifest: dict[str, object] = {
        "schema": 1,
        "provenance": (
            "Clean-room linked graph and original programmatic artwork; no retail "
            "asset bytes are consumed."
        ),
        "address_unit": "16-bit words",
        "bundle_version": "0x80000002",
        "bundle_word_count": len(graph.words),
        "primary_word_count": len(primary),
        "ui_family_a_count": 0,
        "ui_family_b_count": 2,
        "auto_instance": {
            "table_label": "auto_instance_table",
            "marker_words": 4,
            "handle_words": 4,
            "flattened_order": ["settings", "poweroff"],
        },
        "settings": {
            "descriptor": SETTINGS_DESCRIPTOR,
            "brightness_mode": BRIGHTNESS_MODE,
            "brightness_record_count": BRIGHTNESS_LEVELS,
            "brightness_x": BRIGHTNESS_X,
            "volume_mode": VOLUME_MODE,
            "volume_record_count": VOLUME_LEVELS,
            "volume_x": VOLUME_X,
            "y": SETTINGS_Y,
        },
        "poweroff": {
            "descriptor": POWEROFF_DESCRIPTOR,
            "mode": POWEROFF_MODE,
            "record": POWEROFF_RECORD,
            "width": POWEROFF_WIDTH,
            "height": POWEROFF_HEIGHT,
            "chunk_widths": list(CHUNK_WIDTHS),
        },
        "primary": {
            "palette_words": PALETTE_SOURCE_WORDS * 2,
            "settings_image_count": len(settings_images),
            "settings_words_per_image": BITMAP_WORDS,
            "poweroff_chunk_primary_word_offsets": [
                f"{offset:#06x}" for offset in poweroff_chunk_primary_offsets
            ],
        },
        "settings_images": [
            {
                "name": image.name,
                "primary_word_offset": f"{image.primary_word_offset:#06x}",
                "sha256": hashlib.sha256(
                    words_to_bytes(
                        primary[
                            image.primary_word_offset : image.primary_word_offset + BITMAP_WORDS
                        ]
                    )
                ).hexdigest(),
            }
            for image in settings_images
        ],
        "labels": {
            name: f"{offset:#06x}"
            for name, offset in sorted(graph.labels.items(), key=lambda item: item[1])
        },
    }
    return graph.words, primary, manifest


def write_c_output(output: Path, prefix: str, bundle: list[int], primary: list[int]) -> None:
    symbol = c_identifier(prefix)
    upper = symbol.upper()
    guard = f"{upper}_RESOURCES_H"
    header = f"""#ifndef {guard}
#define {guard}

#include "mobigo_sdk/resident_resources.h"
#include "mobigo_sdk/ui_family_b.h"

enum {{
    {upper}_SETTINGS_DESCRIPTOR = {SETTINGS_DESCRIPTOR},
    {upper}_POWEROFF_DESCRIPTOR = {POWEROFF_DESCRIPTOR},
    {upper}_BRIGHTNESS_MODE = {BRIGHTNESS_MODE},
    {upper}_VOLUME_MODE = {VOLUME_MODE},
    {upper}_POWEROFF_MODE = {POWEROFF_MODE},
    {upper}_POWEROFF_RECORD = {POWEROFF_RECORD},
    {upper}_BUNDLE_WORD_COUNT = {len(bundle)},
    {upper}_PRIMARY_WORD_COUNT = {len(primary)}
}};

extern const unsigned short {symbol}_bundle_template[{len(bundle)}];
extern const unsigned short {symbol}_primary_words[{len(primary)}];

void {symbol}_copy_bundle(unsigned short *destination);
void {symbol}_register(unsigned short *writable_bundle);
mg_sdk_ui_handle {symbol}_create_settings(void);
mg_sdk_ui_handle {symbol}_create_poweroff(void);
void {symbol}_show_brightness(mg_sdk_ui_handle handle, unsigned short level);
void {symbol}_show_volume(mg_sdk_ui_handle handle, unsigned short level);
void {symbol}_hide_settings(mg_sdk_ui_handle handle);
void {symbol}_show_poweroff(mg_sdk_ui_handle handle);
void {symbol}_hide_poweroff(mg_sdk_ui_handle handle);

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

void {symbol}_register(unsigned short *writable_bundle)
{{
    mg_sdk_resident_register_asset_bundle(
        writable_bundle,
        (void *){symbol}_primary_words,
        (void *)0);
}}

mg_sdk_ui_handle {symbol}_create_settings(void)
{{
    return mg_sdk_ui_b_create({upper}_SETTINGS_DESCRIPTOR);
}}

mg_sdk_ui_handle {symbol}_create_poweroff(void)
{{
    return mg_sdk_ui_b_create({upper}_POWEROFF_DESCRIPTOR);
}}

static struct mg_sdk_ui_b_object *{symbol}_object(mg_sdk_ui_handle handle)
{{
    return (struct mg_sdk_ui_b_object *)mg_sdk_ui_b_get(handle);
}}

void {symbol}_show_brightness(mg_sdk_ui_handle handle, unsigned short level)
{{
    struct mg_sdk_ui_b_object *object = {symbol}_object(handle);
    if (object == (struct mg_sdk_ui_b_object *)0) {{
        return;
    }}
    if (level >= {BRIGHTNESS_LEVELS}) {{
        level = {BRIGHTNESS_LEVELS - 1};
    }}
    mg_sdk_ui_b_object_prepare(object, {BRIGHTNESS_X}, {SETTINGS_Y}, 0);
    mg_sdk_ui_b_object_show(
        object,
        {upper}_BRIGHTNESS_MODE,
        level,
        {BRIGHTNESS_X},
        {SETTINGS_Y});
}}

void {symbol}_show_volume(mg_sdk_ui_handle handle, unsigned short level)
{{
    struct mg_sdk_ui_b_object *object = {symbol}_object(handle);
    if (object == (struct mg_sdk_ui_b_object *)0) {{
        return;
    }}
    if (level >= {VOLUME_LEVELS}) {{
        level = {VOLUME_LEVELS - 1};
    }}
    mg_sdk_ui_b_object_prepare(object, {VOLUME_X}, {SETTINGS_Y}, 0);
    mg_sdk_ui_b_object_show(
        object,
        {upper}_VOLUME_MODE,
        level,
        {VOLUME_X},
        {SETTINGS_Y});
}}

void {symbol}_hide_settings(mg_sdk_ui_handle handle)
{{
    struct mg_sdk_ui_b_object *object = {symbol}_object(handle);
    if (object != (struct mg_sdk_ui_b_object *)0) {{
        mg_sdk_ui_b_object_hide(object);
    }}
}}

void {symbol}_show_poweroff(mg_sdk_ui_handle handle)
{{
    struct mg_sdk_ui_b_object *object = {symbol}_object(handle);
    if (object == (struct mg_sdk_ui_b_object *)0) {{
        return;
    }}
    mg_sdk_ui_b_object_prepare(object, 160, 120, 1);
    mg_sdk_ui_b_object_show(
        object,
        {upper}_POWEROFF_MODE,
        {upper}_POWEROFF_RECORD,
        160,
        120);
}}

void {symbol}_hide_poweroff(mg_sdk_ui_handle handle)
{{
    struct mg_sdk_ui_b_object *object = {symbol}_object(handle);
    if (object != (struct mg_sdk_ui_b_object *)0) {{
        mg_sdk_ui_b_object_hide(object);
    }}
}}
"""
    (output / f"{prefix}_resources.h").write_text(header, encoding="ascii")
    (output / f"{prefix}_resources.c").write_text(source, encoding="ascii")


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
    parser.add_argument("--prefix", default="mobigo_clean_system_ui")
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
