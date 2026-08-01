#!/usr/bin/env python3
"""Catalog independently recovered retail M/W/S roots and patch directories."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from inspect_asset_bundle import WordImage


@dataclass(frozen=True)
class Sample:
    title: str
    file: str
    runtime_base: int
    title_root: int
    patch_root: int


SAMPLES = (
    Sample("MGB_G1", "BUNDLE_G1_135800G1.MBA", 0x0C8000, 0x10359D, 0x0FF232),
    Sample("MGB_SYS", "BUNDLE_SY_135800SY.MBA", 0x0C8000, 0x0FE7B7, 0x0F93C6),
)


def parse_m_stream(image: WordImage, record: int) -> dict[str, object]:
    byte_length = image.u32(record + 2)
    if byte_length & 1:
        raise ValueError(f"M record {record:#x} has odd byte length")
    words = image.words(record + 10, byte_length // 2)
    index = 0
    events: Counter[str] = Counter()
    end_word = None
    while index < len(words):
        command = words[index]
        index += 1
        event_class = command >> 12
        if event_class == 0:
            if index + 2 > len(words):
                raise ValueError("truncated M note")
            index += 2
            events["note"] += 1
        elif event_class == 1:
            if command & 0x0800:
                if index >= len(words):
                    raise ValueError("truncated M extended wait")
                index += 1
            events["wait"] += 1
        elif event_class == 2:
            if index >= len(words):
                raise ValueError("truncated M skip")
            index += 1
            events["skip"] += 1
        elif event_class == 3:
            if index >= len(words):
                raise ValueError("truncated M control")
            index += 1
            events["control_change"] += 1
        elif event_class == 4:
            events["program_change"] += 1
        elif event_class == 5:
            events["marker"] += 1
        elif event_class == 6:
            events["end"] += 1
            end_word = index - 1
            break
        elif event_class == 7:
            count = command & 0xFF
            if index + 1 + count > len(words):
                raise ValueError("truncated M class-7 block")
            index += 1 + count
            events["aux_control_block"] += 1
        elif event_class == 8:
            count = command & 0xFF
            if index + count > len(words):
                raise ValueError("truncated M class-8 block")
            index += count
            events["aux_block"] += 1
        else:
            raise ValueError(f"unknown M class {event_class:#x}")
    if end_word is None:
        raise ValueError(f"M record {record:#x} has no end command")
    trailing = words[index:]
    if any(word not in (0, 0x00FF, 0xFFFF) for word in trailing):
        raise ValueError(f"M record {record:#x} has non-padding after end")
    return {
        "byte_length": byte_length,
        "events": dict(sorted(events.items())),
        "parsed_words": index,
        "payload_words": len(words),
        "trailing_padding_words": len(trailing),
    }


def catalog_sample(mba_dir: Path, sample: Sample) -> dict[str, object]:
    path = mba_dir / sample.file
    image = WordImage(path, sample.runtime_base)
    m_count = image.u32(sample.title_root)
    w_count = image.u32(sample.title_root + 2)
    s_count = image.u32(sample.title_root + 4)
    total = m_count + w_count + s_count
    pointers = [image.u32(sample.title_root + 6 + index * 2) for index in range(total)]
    terminal_layout = image.u32(sample.title_root + 6 + total * 2)

    expected_classes = [0x004D] * m_count + [0x0057] * w_count + [0x0053] * s_count
    classes = [image.u16(pointer) for pointer in pointers]
    if classes != expected_classes:
        raise ValueError(f"{sample.title}: class ordering mismatch")

    m_records = [parse_m_stream(image, pointer) for pointer in pointers[:m_count]]
    event_totals: Counter[str] = Counter()
    for record in m_records:
        event_totals.update(record["events"])

    w_records: list[dict[str, object]] = []
    for pointer in pointers[m_count : m_count + w_count]:
        words = image.words(pointer, 32)
        tag = words[10:14]
        if tag != [0x5053, 0x3246, 0x4C41, 0x0050]:
            raise ValueError(f"{sample.title}: W SPF tag mismatch at {pointer:#x}")
        w_records.append(
            {
                "address": f"0x{pointer:08x}",
                "byte_length": image.u32(pointer + 2),
                "sample_rate": image.u32(pointer + 18),
                "sample_count": image.u32(pointer + 20),
                "format_flags": f"0x{words[26]:04x}",
                "data_byte_offset": image.u32(pointer + 30),
            }
        )

    s_records: list[dict[str, object]] = []
    for pointer in pointers[m_count + w_count :]:
        byte_length = image.u32(pointer + 2)
        if byte_length % 4:
            raise ValueError(f"{sample.title}: S byte length is not u32-aligned")
        sequence = [image.u32(pointer + 10 + index * 2) for index in range(byte_length // 4)]
        if not sequence or sequence[-1] != 0xFFFFFFFF:
            raise ValueError(f"{sample.title}: S terminator missing")
        s_records.append(
            {
                "address": f"0x{pointer:08x}",
                "byte_length": byte_length,
                "child_count": len(sequence) - 1,
                "children": [f"0x{value:08x}" for value in sequence[:-1]],
            }
        )

    melodic_count = image.u32(sample.patch_root + 10)
    percussion_count_word = sample.patch_root + 12 + melodic_count * 6
    percussion_count = image.u32(percussion_count_word)
    layout_pointer = image.u32(sample.patch_root + 2)

    return {
        "title": sample.title,
        "file": sample.file,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "runtime_base": f"0x{sample.runtime_base:08x}",
        "title_root": f"0x{sample.title_root:08x}",
        "patch_root": f"0x{sample.patch_root:08x}",
        "counts": {"M": m_count, "W": w_count, "S": s_count},
        "terminal_layout": f"0x{terminal_layout:08x}",
        "m_event_totals": dict(sorted(event_totals.items())),
        "m_records": m_records,
        "w_invariants": {
            "record_words": 32,
            "spf_tag": ["0x5053", "0x3246", "0x4c41", "0x0050"],
            "sample_rates": sorted({record["sample_rate"] for record in w_records}),
            "format_flags": sorted({record["format_flags"] for record in w_records}),
        },
        "w_records": w_records,
        "s_records": s_records,
        "patch_directory": {
            "layout_pointer": f"0x{layout_pointer:08x}",
            "melodic_count": melodic_count,
            "percussion_count": percussion_count,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mba-dir", type=Path, default=Path(__file__).resolve().parents[2] / "MBAs")
    parser.add_argument("--output", type=Path, default=Path("research/reports/audio-resource-catalog.json"))
    args = parser.parse_args()
    report = {
        "schema": 1,
        "scope": "Retail roots whose 0x075e06 arguments were independently decompiled in G1 and SY.",
        "samples": [catalog_sample(args.mba_dir, sample) for sample in SAMPLES],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    totals: Counter[str] = Counter()
    for sample in report["samples"]:
        totals.update(sample["counts"])
    print(
        "PASS audio catalog "
        f"samples={len(report['samples'])} M={totals['M']} W={totals['W']} "
        f"S={totals['S']} output={args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
