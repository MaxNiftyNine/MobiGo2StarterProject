#!/usr/bin/env python3
"""Catalog direct far calls into the MobiGo resident service bank.

u'nSP direct far CALL is encoded as two words. For the observed service segment
the first word is 0xf047 and the second is the low 16 bits of the target. The
scanner decodes the general six-bit segment form, then retains only a requested
target range.

MBA bodies mix code and data, so raw opcode scans are candidates. Calls that
land at the same even-spaced service addresses across many independently
linked applications are much stronger evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from collections import Counter, defaultdict
from pathlib import Path


MAGIC = b"bM_gbMQa"
HEADER_WORDS = 0x800
FAR_CALL_MASK = 0xFFC0
FAR_CALL_OPCODE = 0xF040


def parse_int(text: str) -> int:
    return int(text, 0)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("images", type=Path, nargs="+")
    parser.add_argument("--range-start", type=parse_int, default=0x075C00)
    parser.add_argument("--range-end", type=parse_int, default=0x076000)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.range_end <= args.range_start:
        parser.error("range end must be greater than range start")

    images = []
    aggregate_presence: Counter[int] = Counter()
    aggregate_calls: Counter[int] = Counter()

    for path in args.images:
        data = path.read_bytes()
        if len(data) < 0x1000 or len(data) & 1 or data[:8] != MAGIC:
            raise ValueError(f"{path}: not an MBA/GAM")
        _, _, _, entry, body_load = struct.unpack_from("<5I", data, 8)
        runtime_base = body_load - HEADER_WORDS
        words = struct.unpack_from(f"<{len(data) // 2}H", data)
        calls: defaultdict[int, list[int]] = defaultdict(list)

        for offset in range(HEADER_WORDS, len(words) - 1):
            opcode = words[offset]
            if opcode & FAR_CALL_MASK != FAR_CALL_OPCODE:
                continue
            target = ((opcode & 0x3F) << 16) | words[offset + 1]
            if args.range_start <= target < args.range_end:
                calls[target].append(runtime_base + offset)

        for target, sites in calls.items():
            aggregate_presence[target] += 1
            aggregate_calls[target] += len(sites)
        images.append(
            {
                "name": path.name,
                "path": str(path.resolve()),
                "sha256": hashlib.sha256(data).hexdigest(),
                "runtime_base": runtime_base,
                "entry": entry,
                "services": {
                    f"0x{target:06x}": {
                        "call_count": len(sites),
                        "call_sites": sites,
                    }
                    for target, sites in sorted(calls.items())
                },
            }
        )

    report = {
        "schema": 1,
        "warning": "raw opcode candidates; verify important sites in Ghidra",
        "encoding": {
            "mask": FAR_CALL_MASK,
            "opcode": FAR_CALL_OPCODE,
            "target": "((word0 & 0x3f) << 16) | word1",
        },
        "target_range": [args.range_start, args.range_end],
        "image_count": len(images),
        "aggregate": [
            {
                "target": target,
                "images_present": aggregate_presence[target],
                "total_calls": aggregate_calls[target],
            }
            for target in sorted(aggregate_presence)
        ],
        "images": images,
    }
    encoded = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
