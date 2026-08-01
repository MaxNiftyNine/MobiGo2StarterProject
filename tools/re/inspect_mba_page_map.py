#!/usr/bin/env python3
"""Decode the MobiGo 2 launcher footer's physical page-load bitmap."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path


MAGIC = b"bM_gbMQa"
PAGE_BYTES = 0x1000
PAGE_WORDS = PAGE_BYTES // 2
FOOTER_OFFSET = 0xDC0
BITMAP_OFFSET = FOOTER_OFFSET + 0x18
BITMAP_DWORDS = 52


def load_map(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    if (
        len(data) < PAGE_BYTES
        or len(data) % PAGE_BYTES
        or data[: len(MAGIC)] != MAGIC
    ):
        raise ValueError(f"{path}: not a page-aligned MBA/GAM container")
    declared_words = struct.unpack_from("<I", data, 0x08)[0]
    if declared_words * 2 != len(data):
        raise ValueError(f"{path}: declared size does not match file size")

    title = data[0x80:0xA0].split(b"\0", 1)[0].decode(
        "ascii", errors="replace"
    )
    map_begin, map_end = struct.unpack_from("<II", data, FOOTER_OFFSET)
    bitmap = list(
        struct.unpack_from(f"<{BITMAP_DWORDS}I", data, BITMAP_OFFSET)
    )
    set_page_count = sum(value.bit_count() for value in bitmap)
    file_page_count = len(data) // PAGE_BYTES

    if map_begin == 0 and map_end == 0 and set_page_count == 0:
        return {
            "file": path.name,
            "sha256": hashlib.sha256(data).hexdigest(),
            "title": title,
            "kind": "linear_or_legacy",
            "file_page_count": file_page_count,
        }
    if map_begin >= map_end or (map_end - map_begin) % PAGE_WORDS:
        raise ValueError(f"{path}: invalid footer page-map range")
    address_page_count = (map_end - map_begin) // PAGE_WORDS
    if address_page_count > BITMAP_DWORDS * 32:
        raise ValueError(f"{path}: footer page-map range exceeds bitmap")
    for bit in range(address_page_count, BITMAP_DWORDS * 32):
        if bitmap[bit // 32] & (1 << (bit % 32)):
            raise ValueError(f"{path}: set bit lies beyond page-map range")
    if set_page_count != file_page_count:
        raise ValueError(
            f"{path}: bitmap has {set_page_count} pages, "
            f"file has {file_page_count}"
        )

    runs: list[dict[str, object]] = []
    file_page = 0
    bit = 0
    while bit < address_page_count:
        if not (bitmap[bit // 32] & (1 << (bit % 32))):
            bit += 1
            continue
        first = bit
        while bit < address_page_count and (
            bitmap[bit // 32] & (1 << (bit % 32))
        ):
            bit += 1
        count = bit - first
        runtime_begin = map_begin + first * PAGE_WORDS
        runtime_end = runtime_begin + count * PAGE_WORDS
        runs.append(
            {
                "index": len(runs),
                "file_offset": file_page * PAGE_BYTES,
                "byte_length": count * PAGE_BYTES,
                "page_count": count,
                "runtime_word_begin": runtime_begin,
                "runtime_word_end_exclusive": runtime_end,
            }
        )
        file_page += count

    return {
        "file": path.name,
        "sha256": hashlib.sha256(data).hexdigest(),
        "title": title,
        "kind": "footer_page_map",
        "page_bytes": PAGE_BYTES,
        "page_words": PAGE_WORDS,
        "map_word_begin": map_begin,
        "map_word_end_exclusive": map_end,
        "file_page_count": file_page_count,
        "set_page_count": set_page_count,
        "runs": runs,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", type=Path, nargs="+")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    paths: list[Path] = []
    for item in args.inputs:
        if item.is_dir():
            paths.extend(
                path
                for path in sorted(item.iterdir())
                if path.is_file()
                and not path.name.startswith("._")
                and path.suffix.lower() in (".mba", ".gam")
            )
        else:
            paths.append(item)

    report = {
        "schema": 1,
        "address_unit": "16-bit word",
        "classification": (
            "MobiGo 2 launcher footer physical page-load bitmap"
        ),
        "samples": [load_map(path) for path in paths],
    }
    rendered = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
