#!/usr/bin/env python3
"""Catalog recovered linked-asset bundles and standard settings objects."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from array import array
from pathlib import Path


MAGIC = b"bM_gbMQa"
HEADER_WORDS = 0x20
UI_A_WORDS = 10
UI_B_WORDS = 12
STANDARD_PREFIX = [1, 0, 0, 0, 0, 0, 0, 0x40, 0xFFFF, 0xFFFF]
PAGE_BYTES = 0x1000
PAGE_WORDS = PAGE_BYTES // 2
PAGE_BITMAP_OFFSET = 0xDD8
PAGE_BITMAP_DWORDS = 52


def u32(words: array, offset: int) -> int:
    return words[offset] | (words[offset + 1] << 16)


def in_range(words: array, offset: int, count: int = 1) -> bool:
    return 0 <= offset and offset + count <= len(words)


def load(path: Path) -> tuple[bytes, array, int, str]:
    data = path.read_bytes()
    if len(data) < 0x1000 or len(data) & 1 or data[:8] != MAGIC:
        raise ValueError(f"{path}: not an MBA/GAM container")
    words = array("H")
    words.frombytes(data)
    if sys.byteorder != "little":
        words.byteswap()
    body_load = struct.unpack_from("<I", data, 0x18)[0]
    runtime_base = body_load - 0x800
    title = data[0x80:0xA0].split(b"\0", 1)[0].decode(
        "ascii", errors="replace"
    )
    return data, words, runtime_base, title


def page_runs(data: bytes) -> list[dict[str, int]]:
    map_begin, map_end = struct.unpack_from("<II", data, 0xDC0)
    bitmap = struct.unpack_from(
        f"<{PAGE_BITMAP_DWORDS}I", data, PAGE_BITMAP_OFFSET
    )
    if map_begin == 0 and map_end == 0 and not any(bitmap):
        return []
    if (
        map_begin >= map_end
        or (map_end - map_begin) % PAGE_WORDS
        or (map_end - map_begin) // PAGE_WORDS > PAGE_BITMAP_DWORDS * 32
    ):
        return []
    result: list[dict[str, int]] = []
    file_page = 0
    bit = 0
    bit_count = (map_end - map_begin) // PAGE_WORDS
    while bit < bit_count:
        if not (bitmap[bit // 32] & (1 << (bit % 32))):
            bit += 1
            continue
        first = bit
        while bit < bit_count and (
            bitmap[bit // 32] & (1 << (bit % 32))
        ):
            bit += 1
        count = bit - first
        result.append(
            {
                "file_offset": file_page * PAGE_BYTES,
                "byte_length": count * PAGE_BYTES,
                "runtime_begin": map_begin + first * PAGE_WORDS,
                "runtime_end": map_begin + bit * PAGE_WORDS,
            }
        )
        file_page += count
    if file_page * PAGE_BYTES != len(data):
        return []
    return result


def valid_header(words: array, offset: int) -> bool:
    if not in_range(words, offset, HEADER_WORDS):
        return False
    if u32(words, offset) != 0x80000002:
        return False
    lookup_count = words[offset + 0x0A]
    ui_a_count = words[offset + 0x12]
    ui_b_count = words[offset + 0x16]
    if not (0 < lookup_count < 0x4000):
        return False
    if not (0 < ui_a_count < 0x400 and 0 < ui_b_count < 0x400):
        return False
    base = offset + HEADER_WORDS
    lookup = base + u32(words, offset + 0x0C)
    ui_a = base + u32(words, offset + 0x14)
    ui_b = base + u32(words, offset + 0x18)
    return (
        in_range(words, lookup, lookup_count * 2)
        and in_range(words, ui_a, ui_a_count * UI_A_WORDS)
        and in_range(words, ui_b, ui_b_count * UI_B_WORDS)
    )


def signed16(value: int) -> int:
    return value - 0x10000 if value & 0x8000 else value


def bitmap_graph(words: array, base: int, relative: int) -> dict[str, object] | None:
    bitmap = base + relative
    if not in_range(words, bitmap, 6):
        return None
    width = words[bitmap + 1]
    height = words[bitmap + 2]
    chunks = base + u32(words, bitmap + 4)
    if width == 0 or height == 0 or not in_range(words, chunks, 4):
        return None
    target_area = width * height
    covered_area = 0
    result_chunks: list[dict[str, object]] = []
    while covered_area < target_area and len(result_chunks) < 64:
        address = chunks + len(result_chunks) * 4
        if not in_range(words, address, 4):
            return None
        dimensions = words[address]
        chunk_width = dimensions & 0xFF
        chunk_height = dimensions >> 8
        if chunk_width == 0 or chunk_height == 0:
            return None
        result_chunks.append(
            {
                "width": chunk_width,
                "height": chunk_height,
                "flags": f"{words[address + 1]:#06x}",
                "data_pointer": f"{u32(words, address + 2):#010x}",
            }
        )
        covered_area += chunk_width * chunk_height
    if covered_area < target_area:
        return None
    return {
        "relative": f"{relative:#010x}",
        "format_word": f"{words[bitmap]:#06x}",
        "width": width,
        "height": height,
        "chunks": result_chunks,
    }


def setting_records(
    words: array,
    base: int,
    mode: int,
) -> list[dict[str, object]]:
    count = u32(words, mode)
    result: list[dict[str, object]] = []
    for record_index in range(count):
        record = mode + 2 + record_index * 14
        if not in_range(words, record, 14):
            return []
        components = base + u32(words, record + 10)
        if not in_range(words, components, 2):
            return []
        component_count = u32(words, components)
        if component_count == 0 or component_count > 32 or not in_range(
            words, components + 2, component_count * 4
        ):
            return []
        component_results: list[dict[str, object]] = []
        for component_index in range(component_count):
            entry = components + 2 + component_index * 4
            relative = u32(words, entry + 2)
            bitmap = bitmap_graph(words, base, relative)
            if bitmap is None:
                return []
            component_results.append(
                {
                    "index": component_index,
                    "x_offset": signed16(words[entry]),
                    "y_offset": signed16(words[entry + 1]),
                    "bitmap": bitmap,
                }
            )
        result.append(
            {
                "index": record_index,
                "components": component_results,
            }
        )
    return result


def standard_settings(
    words: array,
    header: int,
    descriptor: int,
) -> dict[str, object] | None:
    base = header + HEADER_WORDS
    nested_relative = u32(words, descriptor + 10)
    nested = base + nested_relative
    if not in_range(words, nested, 4):
        return None
    mode_count = u32(words, nested)
    if not (1 <= mode_count <= 8) or not in_range(
        words, nested, 2 + mode_count * 2
    ):
        return None
    modes = [
        base + u32(words, nested + 2 + index * 2)
        for index in range(mode_count)
    ]
    if not all(in_range(words, mode, 2) for mode in modes):
        return None
    counts = [u32(words, mode) for mode in modes]
    if 4 not in counts or 10 not in counts:
        return None

    brightness_mode = counts.index(4)
    volume_mode = counts.index(10)
    brightness_record = modes[brightness_mode] + 2
    components = base + u32(words, brightness_record + 10)
    if not in_range(words, components, 10) or u32(words, components) != 2:
        return None
    first_bitmap = base + u32(words, components + 4)
    if not in_range(words, first_bitmap, 6):
        return None
    chunks = base + u32(words, first_bitmap + 4)
    if not in_range(words, chunks, 8):
        return None

    first_bitmap_graph = bitmap_graph(
        words, base, u32(words, components + 4)
    )
    if first_bitmap_graph is None:
        return None
    return {
        "nested_relative": f"{nested_relative:#010x}",
        "mode_count": mode_count,
        "record_counts_by_mode": counts,
        "brightness_mode": brightness_mode,
        "volume_mode": volume_mode,
        "brightness_component_values": [
            signed16(words[components + 2]),
            signed16(words[components + 6]),
        ],
        "first_brightness_bitmap": first_bitmap_graph,
        "brightness_records": setting_records(
            words, base, modes[brightness_mode]
        ),
        "volume_records": setting_records(words, base, modes[volume_mode]),
    }


def enrich_bitmap_payloads(
    data: bytes,
    primary_run: dict[str, int] | None,
    bitmap: dict[str, object],
) -> None:
    if primary_run is None:
        return
    chunks = bitmap.get("chunks")
    if not isinstance(chunks, list):
        return
    for chunk in chunks:
        if not isinstance(chunk, dict):
            continue
        pointer = int(str(chunk["data_pointer"]), 0)
        if pointer & 0xC0000000 != 0x80000000:
            continue
        byte_length = (
            int(chunk["width"]) * int(chunk["height"]) + 3
        ) // 4
        file_offset = (
            primary_run["file_offset"] + (pointer & 0x3FFFFFFF) * 2
        )
        if file_offset + byte_length > len(data):
            continue
        payload = data[file_offset : file_offset + byte_length]
        chunk["two_bpp_file_offset"] = f"{file_offset:#010x}"
        chunk["two_bpp_byte_length"] = byte_length
        chunk["sha256"] = hashlib.sha256(payload).hexdigest()


def primary_payload(
    data: bytes,
    primary_run: dict[str, int] | None,
    pointer: int,
    byte_length: int,
) -> tuple[int, bytes] | None:
    if primary_run is None or pointer & 0xC0000000 != 0x80000000:
        return None
    file_offset = (
        primary_run["file_offset"] + (pointer & 0x3FFFFFFF) * 2
    )
    if file_offset + byte_length > len(data):
        return None
    return file_offset, data[file_offset : file_offset + byte_length]


def palette_source(
    data: bytes,
    primary_run: dict[str, int] | None,
    pointer: int,
    hardware_begin: int,
) -> dict[str, object]:
    result: dict[str, object] = {
        "pointer": f"{pointer:#010x}",
        "hardware_ranges": [
            f"{hardware_begin:#05x}..{hardware_begin + 0xff:#05x}",
            f"{hardware_begin + 0x200:#05x}..{hardware_begin + 0x2ff:#05x}",
        ],
        "entry_count": 0x200,
    }
    payload = primary_payload(data, primary_run, pointer, 0x400)
    if payload is not None:
        file_offset, contents = payload
        result["file_offset"] = f"{file_offset:#010x}"
        result["sha256"] = hashlib.sha256(contents).hexdigest()
    return result


def enrich_settings_palette(
    data: bytes,
    palette_sources: list[dict[str, object]],
    settings: dict[str, object],
) -> None:
    first = settings.get("first_brightness_bitmap")
    if not isinstance(first, dict):
        return
    format_word = int(str(first["format_word"]), 0)
    high = format_word >> 8
    hardware_index = (
        0x100 + (high & 0x0F) * 0x10 + ((high >> 4) & 1) * 0x200
    )
    palette: dict[str, object] = {
        "default_sprite_hardware_index": f"{hardware_index:#05x}",
        "selector": high & 0x0F,
        "extended_bank": bool(high & 0x10),
    }
    hardware_bank = hardware_index // 0x100
    source_index = hardware_bank & 1
    source_entry = (hardware_bank >> 1) * 0x100 + (hardware_index & 0xFF)
    source = palette_sources[source_index]
    if "file_offset" in source:
        file_offset = (
            int(str(source["file_offset"]), 0) + source_entry * 2
        )
        colors = struct.unpack_from("<4H", data, file_offset)
        palette["source_index"] = source_index
        palette["source_entry"] = f"{source_entry:#05x}"
        palette["file_offset"] = f"{file_offset:#010x}"
        palette["rgb555_words"] = [f"{color:#06x}" for color in colors]
        palette["sha256"] = hashlib.sha256(
            data[file_offset : file_offset + 8]
        ).hexdigest()
    settings["standard_sprite_palette"] = palette


def enrich_settings_payloads(
    data: bytes,
    primary_run: dict[str, int] | None,
    settings: dict[str, object],
) -> None:
    first = settings.get("first_brightness_bitmap")
    if isinstance(first, dict):
        enrich_bitmap_payloads(data, primary_run, first)
    for family in ("brightness_records", "volume_records"):
        records = settings.get(family)
        if not isinstance(records, list):
            continue
        for record in records:
            if not isinstance(record, dict):
                continue
            components = record.get("components")
            if not isinstance(components, list):
                continue
            for component in components:
                if not isinstance(component, dict):
                    continue
                bitmap = component.get("bitmap")
                if isinstance(bitmap, dict):
                    enrich_bitmap_payloads(data, primary_run, bitmap)


def setting_payload_instances(
    sample: dict[str, object],
) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for bundle_index, bundle in enumerate(sample["bundles"]):
        for descriptor in bundle["standard_template_descriptors"]:
            if descriptor["kind"] != "standard_settings":
                continue
            settings = descriptor["settings"]
            for family in ("brightness_records", "volume_records"):
                for record in settings[family]:
                    for component in record["components"]:
                        bitmap = component["bitmap"]
                        for chunk_index, chunk in enumerate(bitmap["chunks"]):
                            if "sha256" not in chunk:
                                continue
                            result.append(
                                {
                                    "file": sample["file"],
                                    "title": sample["title"],
                                    "bundle_index": bundle_index,
                                    "descriptor_index": descriptor["index"],
                                    "family": family,
                                    "record_index": record["index"],
                                    "component_index": component["index"],
                                    "chunk_index": chunk_index,
                                    "format_word": bitmap["format_word"],
                                    "width": chunk["width"],
                                    "height": chunk["height"],
                                    "file_offset": chunk[
                                        "two_bpp_file_offset"
                                    ],
                                    "sha256": chunk["sha256"],
                                }
                            )
    return result


def inspect(path: Path) -> dict[str, object]:
    data, words, runtime_base, title = load(path)
    runs = page_runs(data)
    primary_run = runs[1] if len(runs) >= 2 else None
    headers = [
        offset
        for offset in range(0x800, len(words) - HEADER_WORDS)
        if words[offset] == 2
        and words[offset + 1] == 0x8000
        and valid_header(words, offset)
    ]
    bundles: list[dict[str, object]] = []
    for header in headers:
        base = header + HEADER_WORDS
        palette_sources = [
            palette_source(
                data,
                primary_run,
                u32(words, header + 2),
                0x000,
            ),
            palette_source(
                data,
                primary_run,
                u32(words, header + 4),
                0x100,
            ),
        ]
        ui_b_count = words[header + 0x16]
        ui_b = base + u32(words, header + 0x18)
        templates: list[dict[str, object]] = []
        for index in range(ui_b_count):
            descriptor = ui_b + index * UI_B_WORDS
            settings = standard_settings(words, header, descriptor)
            if settings is not None:
                enrich_settings_payloads(data, primary_run, settings)
                enrich_settings_palette(data, palette_sources, settings)
                item: dict[str, object] = {
                    "index": index,
                    "descriptor_words": [
                        f"{word:#06x}"
                        for word in words[descriptor : descriptor + UI_B_WORDS]
                    ],
                    "nested_relative": f"{u32(words, descriptor + 10):#010x}",
                }
                item["kind"] = "standard_settings"
                item["settings"] = settings
                templates.append(item)
            elif list(words[descriptor : descriptor + 10]) == STANDARD_PREFIX:
                templates.append(
                    {
                        "index": index,
                        "kind": "same_template_other_resource",
                        "nested_relative": (
                            f"{u32(words, descriptor + 10):#010x}"
                        ),
                    }
                )
        bundles.append(
            {
                "header_file_offset": f"{header * 2:#010x}",
                "header_word_address": f"{runtime_base + header:#010x}",
                "lookup_count": words[header + 0x0A],
                "registration_palette_sources": palette_sources,
                "ui_family_a_count": words[header + 0x12],
                "ui_family_b_count": ui_b_count,
                "standard_template_descriptors": templates,
            }
        )
    return {
        "file": path.name,
        "sha256": hashlib.sha256(data).hexdigest(),
        "title": title,
        "runtime_base": f"{runtime_base:#010x}",
        "page_load_runs": [
            {
                key: f"{value:#010x}" if key != "byte_length" else value
                for key, value in run.items()
            }
            for run in runs
        ],
        "bundles": bundles,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", type=Path, nargs="+")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    files: list[Path] = []
    for item in args.inputs:
        if item.is_dir():
            files.extend(
                path
                for path in sorted(item.iterdir())
                if path.is_file()
                and not path.name.startswith("._")
                and path.suffix.lower() in (".mba", ".gam")
            )
        else:
            files.append(item)
    samples = [inspect(path) for path in files]
    payloads_by_hash: dict[str, list[dict[str, object]]] = {}
    for sample in samples:
        for instance in setting_payload_instances(sample):
            payloads_by_hash.setdefault(str(instance["sha256"]), []).append(
                instance
            )
    shared_payloads: dict[str, dict[str, object]] = {}
    for digest, instances in payloads_by_hash.items():
        titles = sorted({str(instance["title"]) for instance in instances})
        if len(titles) < 2:
            continue
        shared_payloads[digest] = {
            "titles": titles,
            "instance_count": len(instances),
            "dimensions": sorted(
                {
                    f"{instance['width']}x{instance['height']}"
                    for instance in instances
                }
            ),
            "uses": instances,
        }
    report = {
        "schema": 3,
        "address_unit": "16-bit word",
        "shared_standard_settings_payloads": shared_payloads,
        "samples": samples,
    }
    rendered = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered)
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
