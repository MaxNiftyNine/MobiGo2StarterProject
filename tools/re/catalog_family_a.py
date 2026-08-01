#!/usr/bin/env python3
"""Catalog linked family-A image records from known asset-bundle headers.

The input catalog is the output of catalog_asset_bundles.py.  This tool only
records structural metadata and pointer values; it does not copy retail image
or tilemap payload data into the report.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from inspect_asset_bundle import WordImage, family_a_image_record, relative_address


def parse_int(value: int | str) -> int:
    if isinstance(value, int):
        return value
    return int(value, 0)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--mba-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
    samples: list[dict[str, object]] = []
    total_descriptors = 0
    total_non_null = 0
    unique_record_shapes: set[tuple[int, ...]] = set()

    for source_sample in catalog.get("samples", []):
        bundles = source_sample.get("bundles", [])
        if not bundles:
            continue
        path = args.mba_dir / str(source_sample["file"])
        if not path.exists():
            raise FileNotFoundError(path)
        runtime_base = parse_int(source_sample["runtime_base"])
        image = WordImage(path, runtime_base)
        sample: dict[str, object] = {
            "file": path.name,
            "title": source_sample.get("title"),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "runtime_base": f"{runtime_base:#010x}",
            "bundles": [],
        }
        for source_bundle in bundles:
            header = parse_int(source_bundle["header_word_address"])
            count = image.u16(header + 0x12)
            table_relative = image.u32(header + 0x14)
            table = relative_address(header, table_relative)
            bundle: dict[str, object] = {
                "header_word_address": f"{header:#010x}",
                "family_a_count": count,
                "family_a_table_relative": f"{table_relative:#010x}",
                "family_a_table_word_address": f"{table:#010x}",
                "descriptors": [],
            }
            total_descriptors += count
            seen_records: dict[tuple[int, ...], int] = {}
            for index in range(count):
                address = table + index * 10
                words = image.words(address, 10)
                nested_relative = words[8] | (words[9] << 16)
                descriptor: dict[str, object] = {
                    "index": index,
                    "word_address": f"{address:#010x}",
                    "words": [f"{word:#06x}" for word in words],
                    "nested_relative": f"{nested_relative:#010x}",
                }
                if nested_relative:
                    total_non_null += 1
                    record = family_a_image_record(image, header, nested_relative)
                    raw_shape = tuple(
                        int(word, 0) for word in record["words"]  # type: ignore[index]
                    )
                    duplicate_of = seen_records.get(raw_shape)
                    if duplicate_of is not None:
                        descriptor["duplicate_record_of"] = duplicate_of
                    else:
                        seen_records[raw_shape] = index
                        unique_record_shapes.add(raw_shape)
                    descriptor["image_record"] = record
                bundle["descriptors"].append(descriptor)  # type: ignore[index]
            sample["bundles"].append(bundle)  # type: ignore[index]
        samples.append(sample)

    report = {
        "schema": 1,
        "address_unit": "16-bit word",
        "family_a_descriptor_words": 10,
        "family_a_image_record_words": 18,
        "proven_fields": {
            "0": "pixel/source width",
            "1": "pixel/source height",
            "2": "cell width",
            "3": "cell height",
            "4": "resident background format selector",
            "10..11": "tagged background graphics-base pointer",
            "12..13": "tagged tilemap/index source pointer",
            "14": "resident background palette selector",
            "16..17": "bundle-relative private two-word runtime slot",
        },
        "unnamed_fields": [5, 6, 7, 8, 9, 15],
        "summary": {
            "descriptor_count": total_descriptors,
            "non_null_descriptor_count": total_non_null,
            "unique_non_null_record_count": len(unique_record_shapes),
        },
        "samples": samples,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
