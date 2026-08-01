#!/usr/bin/env python3
"""Build an original MobiGo-compatible standard settings resource bundle.

The output is a clean-room implementation of the recovered version-2 linked
bundle graph.  It contains newly drawn brightness and volume artwork and does
not read or copy data from an official MBA.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


HEADER_WORDS = 0x20
PALETTE_SOURCE_WORDS = 0x200
UNUSED_RGB555 = 0xCCCC
PRIMARY_TAG = 0x80000000
SECONDARY_TAG = 0xC0000000
BITMAP_WIDTH = 64
BITMAP_HEIGHT = 32
BITMAP_WORDS = BITMAP_WIDTH * BITMAP_HEIGHT // 8
BRIGHTNESS_LEVELS = 4
VOLUME_LEVELS = 10


def u32_words(value: int) -> list[int]:
    if not 0 <= value <= 0xFFFFFFFF:
        raise ValueError(f"32-bit value out of range: {value}")
    return [value & 0xFFFF, value >> 16]


def signed_word(value: int) -> int:
    if not -0x8000 <= value <= 0x7FFF:
        raise ValueError(f"signed word out of range: {value}")
    return value & 0xFFFF


def rgb555(red: int, green: int, blue: int, transparent: bool = False) -> int:
    for name, value in (("red", red), ("green", green), ("blue", blue)):
        if not 0 <= value <= 31:
            raise ValueError(f"{name} must be in the range 0..31")
    return (
        (red << 10)
        | (green << 5)
        | blue
        | (0x8000 if transparent else 0)
    )


class WordBuilder:
    def __init__(self) -> None:
        self.words: list[int] = []
        self.labels: dict[str, int] = {}

    def label(self, name: str) -> int:
        if name in self.labels:
            raise ValueError(f"duplicate label: {name}")
        self.labels[name] = len(self.words)
        return len(self.words)

    def add(self, *words: int) -> int:
        offset = len(self.words)
        for word in words:
            if not 0 <= word <= 0xFFFF:
                raise ValueError(f"word out of range at {offset:#x}: {word}")
            self.words.append(word)
        return offset

    def reserve(self, count: int) -> int:
        offset = len(self.words)
        self.words.extend([0] * count)
        return offset

    def set_u16(self, offset: int, value: int) -> None:
        if not 0 <= value <= 0xFFFF:
            raise ValueError(f"u16 out of range: {value}")
        self.words[offset] = value

    def set_u32(self, offset: int, value: int) -> None:
        low, high = u32_words(value)
        self.words[offset] = low
        self.words[offset + 1] = high

    def relative(self, label: str) -> int:
        value = self.labels[label] - HEADER_WORDS
        if value < 0:
            raise ValueError(f"{label} is inside the bundle header")
        return value

    def set_relative(self, offset: int, label: str) -> None:
        self.set_u32(offset, self.relative(label))


class Canvas:
    def __init__(self, width: int = BITMAP_WIDTH, height: int = BITMAP_HEIGHT):
        self.width = width
        self.height = height
        self.pixels = [0] * (width * height)

    def put(self, x: int, y: int, color: int) -> None:
        if 0 <= x < self.width and 0 <= y < self.height:
            self.pixels[y * self.width + x] = color

    def rect(self, x0: int, y0: int, x1: int, y1: int, color: int) -> None:
        for y in range(y0, y1):
            for x in range(x0, x1):
                self.put(x, y, color)

    def line(self, x0: int, y0: int, x1: int, y1: int, color: int) -> None:
        dx = abs(x1 - x0)
        sx = 1 if x0 < x1 else -1
        dy = -abs(y1 - y0)
        sy = 1 if y0 < y1 else -1
        error = dx + dy
        while True:
            self.put(x0, y0, color)
            if x0 == x1 and y0 == y1:
                break
            twice = error * 2
            if twice >= dy:
                error += dy
                x0 += sx
            if twice <= dx:
                error += dx
                y0 += sy

    def circle(self, cx: int, cy: int, radius: int, color: int) -> None:
        radius_squared = radius * radius
        inner_squared = max(0, (radius - 2) * (radius - 2))
        for y in range(cy - radius, cy + radius + 1):
            for x in range(cx - radius, cx + radius + 1):
                distance = (x - cx) ** 2 + (y - cy) ** 2
                if inner_squared <= distance <= radius_squared:
                    self.put(x, y, color)


def draw_brightness(level: int) -> Canvas:
    canvas = Canvas()
    center_x = 14
    center_y = 16
    radius = 5 + level
    canvas.circle(center_x, center_y, radius, 2)
    if level:
        for dx, dy in (
            (0, -1),
            (1, -1),
            (1, 0),
            (1, 1),
            (0, 1),
            (-1, 1),
            (-1, 0),
            (-1, -1),
        ):
            start = radius + 2
            end = radius + 3 + level
            canvas.line(
                center_x + dx * start,
                center_y + dy * start,
                center_x + dx * end,
                center_y + dy * end,
                3,
            )
    for index in range(BRIGHTNESS_LEVELS):
        x0 = 31 + index * 8
        y0 = 21 - index * 3
        canvas.rect(x0, y0, x0 + 5, 25, 1)
        if index <= level:
            canvas.rect(x0 + 1, y0 + 1, x0 + 4, 24, 3)
    return canvas


def draw_volume(level: int) -> Canvas:
    canvas = Canvas()
    canvas.rect(5, 12, 11, 21, 2)
    for y in range(8, 25):
        reach = min(7, (y - 8) if y < 16 else (24 - y))
        canvas.rect(11, 15 - reach, 18, 18 + reach, 2)
    wave_count = (level + 2) // 3
    for wave in range(wave_count):
        x = 22 + wave * 4
        canvas.line(x, 11 - wave, x + 2, 13, 3)
        canvas.line(x + 2, 13, x + 2, 19, 3)
        canvas.line(x + 2, 19, x, 21 + wave, 3)
    for index in range(VOLUME_LEVELS):
        x0 = 32 + index * 3
        y0 = 22 - index
        canvas.rect(x0, y0, x0 + 2, 25, 1)
        if index < level:
            canvas.rect(x0, y0, x0 + 2, 24, 3)
    if level == 0:
        canvas.line(21, 10, 29, 22, 3)
        canvas.line(29, 10, 21, 22, 3)
    return canvas


def pack_2bpp(pixels: Iterable[int], width: int, height: int) -> bytes:
    values = list(pixels)
    if len(values) != width * height:
        raise ValueError("pixel count does not match dimensions")
    if width % 4:
        raise ValueError("2-bpp row width must be divisible by four")
    packed = bytearray()
    for y in range(height):
        row = values[y * width : (y + 1) * width]
        for x in range(0, width, 4):
            byte = 0
            for index in range(4):
                pixel = row[x + index]
                if not 0 <= pixel <= 3:
                    raise ValueError(f"2-bpp palette index out of range: {pixel}")
                byte |= pixel << (6 - index * 2)
            packed.append(byte)
    return bytes(packed)


def bytes_to_words(data: bytes) -> list[int]:
    if len(data) & 1:
        data += b"\x00"
    return list(struct.unpack(f"<{len(data) // 2}H", data))


def words_to_bytes(words: Iterable[int]) -> bytes:
    values = list(words)
    return struct.pack(f"<{len(values)}H", *values)


def pgm_bytes(canvas: Canvas) -> bytes:
    samples = bytes((0, 85, 170, 255)[value] for value in canvas.pixels)
    return f"P5\n{canvas.width} {canvas.height}\n255\n".encode() + samples


@dataclass
class ImageResource:
    name: str
    canvas: Canvas
    primary_word_offset: int = 0
    lookup_word_offset: int = 0
    component_label: str = ""
    bitmap_label: str = ""
    slot_label: str = ""


def c_identifier(text: str) -> str:
    result = re.sub(r"[^a-zA-Z0-9_]", "_", text)
    if not result or result[0].isdigit():
        result = "_" + result
    return result


def c_words(words: list[int], indent: str = "    ") -> str:
    lines: list[str] = []
    for offset in range(0, len(words), 8):
        chunk = ", ".join(f"0x{word:04x}" for word in words[offset : offset + 8])
        lines.append(indent + chunk + ",")
    return "\n".join(lines)


def write_c_output(
    output: Path,
    prefix: str,
    bundle: list[int],
    primary: list[int],
) -> None:
    symbol = c_identifier(prefix)
    guard = f"{symbol.upper()}_STANDARD_SETTINGS_RESOURCES_H"
    header = f"""#ifndef {guard}
#define {guard}

#include "mobigo_sdk/resident_resources.h"

enum {{
    {symbol.upper()}_SETTINGS_DESCRIPTOR = 0,
    {symbol.upper()}_BRIGHTNESS_MODE = 0,
    {symbol.upper()}_VOLUME_MODE = 1,
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
    return mg_sdk_ui_b_create({symbol.upper()}_SETTINGS_DESCRIPTOR);
}}
"""
    (output / f"{prefix}_resources.h").write_text(header)
    (output / f"{prefix}_resources.c").write_text(source)


def add_record(
    graph: WordBuilder,
    record_offset: int,
    image: ImageResource,
    extent: int,
) -> None:
    fixed = [
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
    graph.words[record_offset : record_offset + 10] = fixed
    graph.set_relative(record_offset + 10, image.component_label)
    graph.set_relative(record_offset + 12, image.slot_label)


def validate_bundle(
    bundle: list[int],
    primary: list[int],
    images: list[ImageResource],
) -> None:
    def read_u32(words: list[int], offset: int) -> int:
        return words[offset] | (words[offset + 1] << 16)

    if read_u32(bundle, 0) != 0x80000002:
        raise ValueError("invalid version-2 state")
    if read_u32(bundle, 2) != PRIMARY_TAG:
        raise ValueError("first palette source does not begin at primary word 0")
    if read_u32(bundle, 4) != PRIMARY_TAG + PALETTE_SOURCE_WORDS:
        raise ValueError("second palette source is not at primary word 0x200")
    if bundle[0x0A] != len(images):
        raise ValueError("lookup count does not match generated images")
    if bundle[0x12] != 0 or bundle[0x16] != 1:
        raise ValueError("unexpected UI-family counts")
    if len(primary) < PALETTE_SOURCE_WORDS * 2:
        raise ValueError("primary image is too short for two palettes")
    selected = primary[PALETTE_SOURCE_WORDS : PALETTE_SOURCE_WORDS + 4]
    if not (selected[0] & 0x8000):
        raise ValueError("palette index zero must be transparent")
    lookup = HEADER_WORDS + read_u32(bundle, 0x0C)
    for index, image in enumerate(images):
        entry = lookup + index * 4
        if bundle[entry] != (BITMAP_HEIGHT << 8) | BITMAP_WIDTH:
            raise ValueError(f"{image.name}: invalid chunk dimensions")
        pointer = read_u32(bundle, entry + 2)
        if pointer != PRIMARY_TAG + image.primary_word_offset:
            raise ValueError(f"{image.name}: invalid primary pointer")
        begin = image.primary_word_offset
        end = begin + BITMAP_WORDS
        if end > len(primary):
            raise ValueError(f"{image.name}: pixel data is outside primary image")


def build_resources() -> tuple[list[int], list[int], dict[str, object], list[ImageResource]]:
    images = [
        ImageResource(f"brightness_{level}", draw_brightness(level))
        for level in range(BRIGHTNESS_LEVELS)
    ]
    images.extend(
        ImageResource(f"volume_{level}", draw_volume(level))
        for level in range(VOLUME_LEVELS)
    )

    even_palette = [UNUSED_RGB555] * PALETTE_SOURCE_WORDS
    odd_palette = [UNUSED_RGB555] * PALETTE_SOURCE_WORDS
    odd_palette[:4] = [
        rgb555(0, 0, 0, transparent=True),
        rgb555(4, 7, 12),
        rgb555(31, 31, 31),
        rgb555(31, 18, 3),
    ]
    primary = even_palette + odd_palette
    for image in images:
        image.primary_word_offset = len(primary)
        primary.extend(bytes_to_words(pack_2bpp(
            image.canvas.pixels, image.canvas.width, image.canvas.height
        )))

    graph = WordBuilder()
    graph.reserve(HEADER_WORDS)
    graph.label("lookup")
    lookup_offset = graph.reserve(len(images) * 4)
    graph.label("aux_and_ui_a_empty")
    graph.label("ui_b_table")
    descriptor_offset = graph.reserve(12)
    graph.label("auto_instance_table")
    graph.label("generated_handles")
    graph.reserve(4)
    graph.label("settings_modes")
    mode_table_offset = graph.add(*u32_words(2), 0, 0, 0, 0)
    graph.label("brightness_records")
    brightness_offset = graph.add(*u32_words(BRIGHTNESS_LEVELS))
    graph.reserve(BRIGHTNESS_LEVELS * 14)
    graph.label("volume_records")
    volume_offset = graph.add(*u32_words(VOLUME_LEVELS))
    graph.reserve(VOLUME_LEVELS * 14)

    for index, image in enumerate(images):
        image.lookup_word_offset = lookup_offset + index * 4
        image.component_label = f"{image.name}_components"
        image.bitmap_label = f"{image.name}_bitmap"
        image.slot_label = f"{image.name}_runtime_slot"

        graph.label(image.component_label)
        component_offset = graph.add(*u32_words(1), 0, 0, 0, 0)
        graph.label(image.bitmap_label)
        bitmap_offset = graph.add(
            0x0000,
            BITMAP_WIDTH,
            BITMAP_HEIGHT,
            0,
            0,
            0,
        )
        graph.label(image.slot_label)
        graph.add(0, 0)
        graph.set_relative(component_offset + 4, image.bitmap_label)
        graph.set_u32(
            bitmap_offset + 4,
            image.lookup_word_offset - HEADER_WORDS,
        )

        entry = image.lookup_word_offset
        graph.set_u16(entry, (BITMAP_HEIGHT << 8) | BITMAP_WIDTH)
        graph.set_u16(entry + 1, 0)
        graph.set_u32(entry + 2, PRIMARY_TAG + image.primary_word_offset)

    graph.set_u32(0x00, 0x80000002)
    graph.set_u32(0x02, PRIMARY_TAG)
    graph.set_u32(0x04, PRIMARY_TAG + PALETTE_SOURCE_WORDS)
    graph.set_u32(0x06, SECONDARY_TAG)
    graph.set_u32(0x08, SECONDARY_TAG + 0x100)
    graph.set_u16(0x0A, len(images))
    graph.set_relative(0x0C, "lookup")
    graph.set_relative(0x10, "aux_and_ui_a_empty")
    graph.set_u16(0x12, 0)
    graph.set_relative(0x14, "aux_and_ui_a_empty")
    graph.set_u16(0x16, 1)
    graph.set_relative(0x18, "ui_b_table")
    graph.set_relative(0x1A, "generated_handles")

    descriptor = [
        0x0001,
        0,
        0,
        0,
        0,
        0,
        0,
        0x0040,
        0xFFFF,
        0xFFFF,
        0,
        0,
    ]
    graph.words[descriptor_offset : descriptor_offset + 12] = descriptor
    graph.set_relative(descriptor_offset + 10, "settings_modes")
    graph.set_relative(mode_table_offset + 2, "brightness_records")
    graph.set_relative(mode_table_offset + 4, "volume_records")

    for level, image in enumerate(images[:BRIGHTNESS_LEVELS]):
        add_record(graph, brightness_offset + 2 + level * 14, image, 0x002C)
    for level, image in enumerate(images[BRIGHTNESS_LEVELS:]):
        add_record(graph, volume_offset + 2 + level * 14, image, 0x006B)

    validate_bundle(graph.words, primary, images)
    manifest: dict[str, object] = {
        "schema": 1,
        "provenance": (
            "Clean-room graph and original programmatic artwork; no retail "
            "asset bytes are consumed."
        ),
        "address_unit": "16-bit words",
        "bundle_version": "0x80000002",
        "bundle_word_count": len(graph.words),
        "primary_word_count": len(primary),
        "palette_sources": [
            {
                "primary_word_offset": "0x0000",
                "hardware_ranges": ["0x000..0x0ff", "0x200..0x2ff"],
                "entry_count": PALETTE_SOURCE_WORDS,
            },
            {
                "primary_word_offset": "0x0200",
                "hardware_ranges": ["0x100..0x1ff", "0x300..0x3ff"],
                "entry_count": PALETTE_SOURCE_WORDS,
                "settings_palette_entry": "0x000",
                "settings_rgb555": [f"0x{word:04x}" for word in odd_palette[:4]],
            },
        ],
        "ui_family_b_descriptor": 0,
        "brightness_mode": 0,
        "volume_mode": 1,
        "brightness_record_count": BRIGHTNESS_LEVELS,
        "volume_record_count": VOLUME_LEVELS,
        "images": [
            {
                "name": image.name,
                "width": image.canvas.width,
                "height": image.canvas.height,
                "format_word": "0x0000",
                "lookup_index": index,
                "primary_word_offset": f"{image.primary_word_offset:#06x}",
                "packed_sha256": hashlib.sha256(
                    words_to_bytes(
                        primary[
                            image.primary_word_offset :
                            image.primary_word_offset + BITMAP_WORDS
                        ]
                    )
                ).hexdigest(),
            }
            for index, image in enumerate(images)
        ],
        "labels": {
            name: f"{offset:#06x}"
            for name, offset in sorted(graph.labels.items(), key=lambda item: item[1])
        },
    }
    return graph.words, primary, manifest, images


def write_outputs(output: Path, prefix: str) -> dict[str, object]:
    bundle, primary, manifest, images = build_resources()
    output.mkdir(parents=True, exist_ok=True)
    preview = output / "previews"
    preview.mkdir(exist_ok=True)
    (output / "bundle.bin").write_bytes(words_to_bytes(bundle))
    (output / "primary.bin").write_bytes(words_to_bytes(primary))
    for image in images:
        (preview / f"{image.name}.pgm").write_bytes(pgm_bytes(image.canvas))
    write_c_output(output, prefix, bundle, primary)
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Build a clean-room version-2 bundle containing original "
            "brightness and volume artwork"
        )
    )
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--prefix",
        default="mobigo_clean_settings",
        help="basename and C symbol prefix (default: %(default)s)",
    )
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
