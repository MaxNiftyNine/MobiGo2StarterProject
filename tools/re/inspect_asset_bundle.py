#!/usr/bin/env python3
"""Inspect recovered MobiGo linked-asset bundle metadata without extracting assets."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_int(text: str) -> int:
    return int(text, 0)


class WordImage:
    def __init__(self, path: Path, runtime_base: int) -> None:
        self.path = path
        self.runtime_base = runtime_base
        self.data = path.read_bytes()
        if len(self.data) & 1:
            raise ValueError("MBA size is not an even number of bytes")

    def offset(self, word_address: int) -> int:
        result = (word_address - self.runtime_base) * 2
        if result < 0 or result + 2 > len(self.data):
            raise ValueError(f"word address {word_address:#x} is outside the MBA")
        return result

    def u16(self, word_address: int) -> int:
        offset = self.offset(word_address)
        return int.from_bytes(self.data[offset : offset + 2], "little")

    def u32(self, word_address: int) -> int:
        return self.u16(word_address) | (self.u16(word_address + 1) << 16)

    def words(self, word_address: int, count: int) -> list[int]:
        return [self.u16(word_address + index) for index in range(count)]


def relative_address(header: int, relative: int) -> int:
    return header + 0x20 + relative


def descriptor(
    image: WordImage,
    table: int,
    index: int,
    stride: int,
) -> dict[str, object]:
    address = table + index * stride
    words = image.words(address, stride)
    result: dict[str, object] = {
        "index": index,
        "word_address": f"{address:#010x}",
        "words": [f"{word:#06x}" for word in words],
    }
    if stride == 12:
        result["nested_relative"] = f"{words[10] | (words[11] << 16):#010x}"
    elif stride == 10:
        result["nested_relative"] = f"{words[8] | (words[9] << 16):#010x}"
    return result


def family_a_image_record(
    image: WordImage,
    header: int,
    nested_relative: int,
) -> dict[str, object]:
    address = relative_address(header, nested_relative)
    words = image.words(address, 18)
    graphics_base = words[10] | (words[11] << 16)
    tilemap_source = words[12] | (words[13] << 16)
    runtime_slot_relative = words[16] | (words[17] << 16)
    runtime_slot_address = relative_address(header, runtime_slot_relative)
    return {
        "relative": f"{nested_relative:#010x}",
        "word_address": f"{address:#010x}",
        "words": [f"{word:#06x}" for word in words],
        "width": words[0],
        "height": words[1],
        "cell_width": words[2],
        "cell_height": words[3],
        "format": words[4],
        "graphics_base_pointer": f"{graphics_base:#010x}",
        "tilemap_source_pointer": f"{tilemap_source:#010x}",
        "palette_selector": words[14],
        "runtime_slot_relative": f"{runtime_slot_relative:#010x}",
        "runtime_slot_word_address": f"{runtime_slot_address:#010x}",
        "runtime_slot_words": [
            f"{word:#06x}" for word in image.words(runtime_slot_address, 2)
        ],
    }


def signed16(value: int) -> int:
    return value - 0x10000 if value & 0x8000 else value


def bitmap_graph(
    image: WordImage,
    header: int,
    bitmap_relative: int,
) -> dict[str, object]:
    bitmap_address = relative_address(header, bitmap_relative)
    words = image.words(bitmap_address, 6)
    chunk_relative = words[4] | (words[5] << 16)
    chunk_address = relative_address(header, chunk_relative)
    target_area = words[1] * words[2]
    covered_area = 0
    chunks: list[dict[str, object]] = []
    while covered_area < target_area and len(chunks) < 64:
        current = chunk_address + len(chunks) * 4
        dimensions = image.u16(current)
        width = dimensions & 0xFF
        height = dimensions >> 8
        if width == 0 or height == 0:
            break
        data_pointer = image.u32(current + 2)
        chunks.append(
            {
                "word_address": f"{current:#010x}",
                "width": width,
                "height": height,
                "flags": f"{image.u16(current + 1):#06x}",
                "data_pointer": f"{data_pointer:#010x}",
            }
        )
        covered_area += width * height
    return {
        "relative": f"{bitmap_relative:#010x}",
        "word_address": f"{bitmap_address:#010x}",
        "format": f"{words[0]:#06x}",
        "width": words[1],
        "height": words[2],
        "reserved": f"{words[3]:#06x}",
        "chunk_table_relative": f"{chunk_relative:#010x}",
        "chunks": chunks,
    }


def first_setting_record_graph(
    image: WordImage,
    header: int,
    mode_address: int,
) -> dict[str, object]:
    record_address = mode_address + 2
    component_relative = image.u32(record_address + 10)
    component_address = relative_address(header, component_relative)
    component_count = image.u32(component_address)
    components: list[dict[str, object]] = []
    for index in range(component_count):
        entry = component_address + 2 + index * 4
        value = image.u16(entry)
        bitmap_relative = image.u32(entry + 2)
        components.append(
            {
                "value": signed16(value),
                "reserved": f"{image.u16(entry + 1):#06x}",
                "bitmap": bitmap_graph(image, header, bitmap_relative),
            }
        )
    return {
        "record_word_address": f"{record_address:#010x}",
        "component_list_relative": f"{component_relative:#010x}",
        "component_list_word_address": f"{component_address:#010x}",
        "component_count": component_count,
        "components": components,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect the recovered 0x20-word MBA asset-bundle header"
    )
    parser.add_argument("mba", type=Path)
    parser.add_argument("--runtime-base", type=parse_int, default=0xC8000)
    parser.add_argument("--header-word", type=parse_int, required=True)
    parser.add_argument("--family-a-index", type=parse_int)
    parser.add_argument("--settings-index", type=parse_int)
    parser.add_argument("--poweroff-index", type=parse_int)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    image = WordImage(args.mba, args.runtime_base)
    header = args.header_word
    header_words = image.words(header, 0x20)
    lookup_relative = image.u32(header + 0x0C)
    family_a_relative = image.u32(header + 0x14)
    family_b_relative = image.u32(header + 0x18)
    family_a_table = relative_address(header, family_a_relative)
    family_b_table = relative_address(header, family_b_relative)

    result: dict[str, object] = {
        "schema": 1,
        "mba": str(args.mba),
        "runtime_base": f"{args.runtime_base:#010x}",
        "header_word_address": f"{header:#010x}",
        "header_file_offset": f"{image.offset(header):#010x}",
        "header_words": [f"{word:#06x}" for word in header_words],
        "state": f"{image.u32(header):#010x}",
        "lookup_count": image.u16(header + 0x0A),
        "lookup_table_relative": f"{lookup_relative:#010x}",
        "lookup_table_word_address": (
            f"{relative_address(header, lookup_relative):#010x}"
        ),
        "ui_family_a_count": image.u16(header + 0x12),
        "ui_family_a_table_relative": f"{family_a_relative:#010x}",
        "ui_family_a_table_word_address": f"{family_a_table:#010x}",
        "ui_family_b_count": image.u16(header + 0x16),
        "ui_family_b_table_relative": f"{family_b_relative:#010x}",
        "ui_family_b_table_word_address": f"{family_b_table:#010x}",
    }

    descriptors: dict[str, object] = {}
    for name, index in (
        ("settings", args.settings_index),
        ("poweroff", args.poweroff_index),
    ):
        if index is None:
            continue
        info = descriptor(image, family_b_table, index, 12)
        nested_relative = int(str(info["nested_relative"]), 0)
        info["nested_word_address"] = (
            f"{relative_address(header, nested_relative):#010x}"
        )
        descriptors[name] = info
    if descriptors:
        result["ui_family_b_descriptors"] = descriptors

    if args.family_a_index is not None:
        info = descriptor(image, family_a_table, args.family_a_index, 10)
        nested_relative = int(str(info["nested_relative"]), 0)
        info["nested_word_address"] = (
            f"{relative_address(header, nested_relative):#010x}"
        )
        info["image_record"] = family_a_image_record(
            image, header, nested_relative
        )
        result["ui_family_a_descriptor"] = info

    if args.settings_index is not None:
        settings = descriptors["settings"]
        settings_address = int(str(settings["nested_word_address"]), 0)
        mode_count = image.u32(settings_address)
        mode_relative = [
            image.u32(settings_address + 2 + index * 2)
            for index in range(mode_count)
        ]
        modes: list[dict[str, object]] = []
        for index, relative in enumerate(mode_relative):
            address = relative_address(header, relative)
            mode: dict[str, object] = {
                "index": index,
                "relative": f"{relative:#010x}",
                "word_address": f"{address:#010x}",
                "record_count": image.u32(address),
            }
            if mode["record_count"] in (4, 10):
                mode["first_record_graph"] = first_setting_record_graph(
                    image, header, address
                )
            modes.append(mode)
        result["standard_settings"] = {
            "mode_count": mode_count,
            "modes": modes,
        }

    if args.poweroff_index is not None:
        poweroff = descriptors["poweroff"]
        root_address = int(str(poweroff["nested_word_address"]), 0)
        mode_count = image.u32(root_address)
        modes: list[dict[str, object]] = []
        for index in range(mode_count):
            relative = image.u32(root_address + 2 + index * 2)
            address = relative_address(header, relative)
            record_count = image.u32(address)
            mode: dict[str, object] = {
                "index": index,
                "relative": f"{relative:#010x}",
                "word_address": f"{address:#010x}",
                "record_count": record_count,
            }
            if record_count:
                mode["first_record_graph"] = first_setting_record_graph(
                    image, header, address
                )
            modes.append(mode)
        result["standard_poweroff"] = {
            "mode_count": mode_count,
            "modes": modes,
        }

    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered)
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
