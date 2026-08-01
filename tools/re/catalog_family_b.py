#!/usr/bin/env python3
"""Catalog all primary family-B mode/record graphs in known MBA bundles."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from inspect_asset_bundle import WordImage, relative_address, signed16


def parse_int(value: int | str) -> int:
    return value if isinstance(value, int) else int(value, 0)


def counter_json(counter: Counter[int]) -> dict[str, int]:
    return {
        str(key): value
        for key, value in sorted(counter.items(), key=lambda item: (item[0]))
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--mba-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    source = json.loads(args.catalog.read_text(encoding="utf-8"))
    total_descriptors = 0
    non_null_descriptors = 0
    total_modes = 0
    total_records = 0
    records_with_delta = 0
    word7 = Counter()
    event_tokens = Counter()
    durations = Counter()
    min_x = Counter()
    max_x = Counter()
    min_y = Counter()
    max_y = Counter()
    component_counts = Counter()
    component_count_total = 0
    bitmap_formats = Counter()
    bitmap_format_codes = Counter()
    bitmap_reserved = Counter()
    chunk_flags = Counter()
    chunk_pointer_classes = Counter()
    chunk_widths = Counter()
    chunk_heights = Counter()
    chunk_dimensions = Counter()
    unique_component_lists: set[tuple[str, int, int]] = set()
    unique_bitmaps: set[tuple[str, int, int]] = set()
    total_unique_chunks = 0
    samples: list[dict[str, object]] = []

    for source_sample in source.get("samples", []):
        bundles = source_sample.get("bundles", [])
        if not bundles:
            continue
        runtime_base = parse_int(source_sample["runtime_base"])
        image = WordImage(args.mba_dir / str(source_sample["file"]), runtime_base)
        sample_record_count = 0
        sample_descriptor_count = 0
        sample_modes = 0
        descriptor_summaries: list[dict[str, object]] = []

        for source_bundle in bundles:
            header = parse_int(source_bundle["header_word_address"])
            descriptor_count = image.u16(header + 0x16)
            table = relative_address(header, image.u32(header + 0x18))
            total_descriptors += descriptor_count
            sample_descriptor_count += descriptor_count

            for descriptor_index in range(descriptor_count):
                descriptor = image.words(table + descriptor_index * 12, 12)
                nested_relative = descriptor[10] | (descriptor[11] << 16)
                if nested_relative == 0:
                    descriptor_summaries.append(
                        {
                            "header_word_address": f"{header:#010x}",
                            "descriptor": descriptor_index,
                            "nested_relative": "0x00000000",
                            "mode_count": 0,
                            "record_count": 0,
                        }
                    )
                    continue

                non_null_descriptors += 1
                root = relative_address(header, nested_relative)
                mode_count = image.u32(root)
                if mode_count > 0x100:
                    raise ValueError(
                        f"implausible family-B mode count {mode_count} "
                        f"at {root:#x}"
                    )
                total_modes += mode_count
                sample_modes += mode_count
                descriptor_records = 0
                mode_record_counts: list[int] = []

                for mode_index in range(mode_count):
                    mode_relative = image.u32(root + 2 + mode_index * 2)
                    mode = relative_address(header, mode_relative)
                    record_count = image.u32(mode)
                    if record_count > 0x1000:
                        raise ValueError(
                            f"implausible record count {record_count} at {mode:#x}"
                        )
                    mode_record_counts.append(record_count)
                    descriptor_records += record_count
                    total_records += record_count
                    sample_record_count += record_count

                    for record_index in range(record_count):
                        words = image.words(mode + 2 + record_index * 14, 14)
                        dx = signed16(words[0])
                        dy = signed16(words[1])
                        if dx or dy:
                            records_with_delta += 1
                        durations[words[2]] += 1
                        min_y[signed16(words[3])] += 1
                        max_y[signed16(words[4])] += 1
                        min_x[signed16(words[5])] += 1
                        max_x[signed16(words[6])] += 1
                        word7[words[7]] += 1
                        event = words[8] | (words[9] << 16)
                        event_tokens[event] += 1

                        # The common grammar requires a counted component-list
                        # pointer in words 10..11 and a private runtime pointer
                        # in words 12..13. Validate both land inside the image.
                        for pair in (10, 12):
                            relative = words[pair] | (words[pair + 1] << 16)
                            address = relative_address(header, relative)
                            image.words(address, 2)

                        component_relative = words[10] | (words[11] << 16)
                        component_address = relative_address(header, component_relative)
                        component_count = image.u32(component_address)
                        if component_count > 0x100:
                            raise ValueError(
                                f"implausible component count {component_count} "
                                f"at {component_address:#x}"
                            )
                        component_counts[component_count] += 1
                        component_count_total += component_count
                        unique_component_lists.add(
                            (str(source_sample["file"]), header, component_address)
                        )

                        for component_index in range(component_count):
                            component = image.words(
                                component_address + 2 + component_index * 4, 4
                            )
                            bitmap_relative = component[2] | (component[3] << 16)
                            bitmap_address = relative_address(header, bitmap_relative)
                            bitmap_key = (
                                str(source_sample["file"]),
                                header,
                                bitmap_address,
                            )
                            if bitmap_key in unique_bitmaps:
                                continue
                            unique_bitmaps.add(bitmap_key)
                            bitmap = image.words(bitmap_address, 6)
                            bitmap_formats[bitmap[0]] += 1
                            bitmap_format_codes[bitmap[0] & 0x00ff] += 1
                            bitmap_reserved[bitmap[3]] += 1

                            chunk_relative = bitmap[4] | (bitmap[5] << 16)
                            chunk_address = relative_address(header, chunk_relative)
                            target_area = bitmap[1] * bitmap[2]
                            covered_area = 0
                            chunk_index = 0
                            while covered_area < target_area:
                                if chunk_index >= 0x800:
                                    raise ValueError(
                                        f"too many chunks for bitmap {bitmap_address:#x}"
                                    )
                                chunk = image.words(
                                    chunk_address + chunk_index * 4, 4
                                )
                                width = chunk[0] & 0xff
                                height = chunk[0] >> 8
                                if width == 0 or height == 0:
                                    raise ValueError(
                                        f"zero-sized chunk for bitmap {bitmap_address:#x}"
                                    )
                                chunk_flags[chunk[1]] += 1
                                chunk_widths[width] += 1
                                chunk_heights[height] += 1
                                chunk_dimensions[(width, height)] += 1
                                pointer = chunk[2] | (chunk[3] << 16)
                                chunk_pointer_classes[(pointer >> 30) & 3] += 1
                                total_unique_chunks += 1
                                covered_area += width * height
                                chunk_index += 1

                descriptor_summaries.append(
                    {
                        "header_word_address": f"{header:#010x}",
                        "descriptor": descriptor_index,
                        "nested_relative": f"{nested_relative:#010x}",
                        "mode_count": mode_count,
                        "record_count": descriptor_records,
                        "mode_record_counts": mode_record_counts,
                    }
                )

        samples.append(
            {
                "title": source_sample.get("title"),
                "file": source_sample.get("file"),
                "descriptor_count": sample_descriptor_count,
                "mode_count": sample_modes,
                "record_count": sample_record_count,
                "descriptors": descriptor_summaries,
            }
        )

    report = {
        "schema": 1,
        "address_unit": "16-bit word",
        "family_b_descriptor_words": 12,
        "family_b_record_words": 14,
        "summary": {
            "descriptor_count": total_descriptors,
            "non_null_descriptor_count": non_null_descriptors,
            "mode_count": total_modes,
            "record_count": total_records,
            "records_with_nonzero_delta": records_with_delta,
            "word7_distribution": counter_json(word7),
            "transition_token_distribution": {
                f"{key:#010x}": value
                for key, value in sorted(event_tokens.items())
            },
            "duration_distribution": counter_json(durations),
            "min_x_distribution": counter_json(min_x),
            "max_x_distribution": counter_json(max_x),
            "min_y_distribution": counter_json(min_y),
            "max_y_distribution": counter_json(max_y),
            "component_count_distribution": counter_json(component_counts),
            "component_reference_count": component_count_total,
            "unique_component_list_count": len(unique_component_lists),
            "unique_bitmap_count": len(unique_bitmaps),
            "bitmap_format_distribution": {
                f"{key:#06x}": value
                for key, value in sorted(bitmap_formats.items())
            },
            "bitmap_format_code_distribution": counter_json(bitmap_format_codes),
            "bitmap_reserved_word_distribution": {
                f"{key:#06x}": value
                for key, value in sorted(bitmap_reserved.items())
            },
            "unique_chunk_count": total_unique_chunks,
            "chunk_flag_distribution": {
                f"{key:#06x}": value
                for key, value in sorted(chunk_flags.items())
            },
            "chunk_pointer_class_distribution": counter_json(chunk_pointer_classes),
            "chunk_width_distribution": counter_json(chunk_widths),
            "chunk_height_distribution": counter_json(chunk_heights),
            "chunk_dimension_distribution": {
                f"{width}x{height}": count
                for (width, height), count in sorted(chunk_dimensions.items())
            },
        },
        "resident_confirmed_record_fields": {
            "0": "signed X delta applied when advancing records",
            "1": "signed Y delta applied when advancing records",
            "2": "record duration/tick span",
            "3": "signed minimum Y bound relative to object anchor",
            "4": "signed maximum Y bound relative to object anchor",
            "5": "signed minimum X bound relative to object anchor",
            "6": "signed maximum X bound relative to object anchor",
            "7": "reserved/zero in every catalogued primary record",
            "8..9": "optional 32-bit transition token; 0xffffffff in every catalogued primary record",
            "10..11": "bundle-relative counted component-list pointer",
            "12..13": "bundle-relative private mutable runtime-slot pointer",
        },
        "samples": samples,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        "PASS "
        f"descriptors={total_descriptors} non_null={non_null_descriptors} "
        f"modes={total_modes} records={total_records} output={args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
