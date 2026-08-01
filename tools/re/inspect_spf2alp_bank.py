#!/usr/bin/env python3
"""Inspect the shared SPF2ALP sound-patch bank found in MobiGo software.

This is a metadata-only clean-room inspection tool.  It does not decode or
extract retail audio.  The field names remain deliberately conservative until
the corresponding playback code has been recovered.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path


MAGIC = b"bM_gbMQa"
ZONE_SIZE = 0x44
ZONE_TAG = b"SPF2ALP\0"


def u32(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


@dataclass(frozen=True)
class DirectoryEntry:
    bank: str
    resource_id: int | None
    data_offset: int
    byte_length: int


@dataclass(frozen=True)
class Zone:
    offset: int
    key_low: int
    key_high: int
    settings: int
    data_begin: int
    level_pair: int
    raw_10: int
    data_end: int
    tag: str
    signature_a: int
    signature_b: int
    playback_value: int
    raw_2c: int
    frame_or_sample_count: int
    raw_34: int
    trailing_parameters: int
    trailing_format: int
    raw_40: int


@dataclass(frozen=True)
class Group:
    bank: str
    resource_id: int | None
    data_offset: int
    byte_length: int
    zone_count: int
    header_size: int
    zone_offsets: list[int]
    zones: list[Zone]


def parse_directory(
    block: bytes,
) -> tuple[int, list[DirectoryEntry], int, list[DirectoryEntry], int]:
    """Parse the two directories and return their entries plus data base.

    In the observed bank, the first directory count includes one implicit
    resource at data offset zero.  Its size is stored at block+0x18.  The
    remaining entries are conventional {id, offset, length} triples.
    """
    if len(block) < 0x40:
        raise ValueError("block is too short for an SPF2ALP bank")

    primary_count = u32(block, 0x0C)
    implicit_length = u32(block, 0x18)
    if not 1 <= primary_count <= 0x1000 or implicit_length == 0:
        raise ValueError("implausible primary directory header")

    primary = [
        DirectoryEntry(
            bank="primary",
            resource_id=None,
            data_offset=0,
            byte_length=implicit_length,
        )
    ]
    cursor = 0x1C
    for _ in range(primary_count - 1):
        primary.append(
            DirectoryEntry(
                bank="primary",
                resource_id=u32(block, cursor),
                data_offset=u32(block, cursor + 4),
                byte_length=u32(block, cursor + 8),
            )
        )
        cursor += 12

    secondary_count = u32(block, cursor)
    cursor += 4
    if secondary_count > 0x1000:
        raise ValueError("implausible secondary directory count")

    secondary = []
    for _ in range(secondary_count):
        secondary.append(
            DirectoryEntry(
                bank="secondary",
                resource_id=u32(block, cursor),
                data_offset=u32(block, cursor + 4),
                byte_length=u32(block, cursor + 8),
            )
        )
        cursor += 12

    return primary_count, primary, secondary_count, secondary, cursor


def parse_zone(block: bytes, offset: int) -> Zone:
    raw = block[offset:offset + ZONE_SIZE]
    if len(raw) != ZONE_SIZE:
        raise ValueError(f"truncated zone at block offset 0x{offset:x}")

    key_range = u32(raw, 0)
    tag_bytes = raw[0x18:0x20]
    return Zone(
        offset=offset,
        key_low=key_range & 0xFF,
        key_high=(key_range >> 8) & 0xFF,
        settings=u32(raw, 0x04),
        data_begin=u32(raw, 0x08),
        level_pair=u32(raw, 0x0C),
        raw_10=u32(raw, 0x10),
        data_end=u32(raw, 0x14),
        tag=tag_bytes.rstrip(b"\0").decode("ascii", errors="replace"),
        signature_a=u32(raw, 0x20),
        signature_b=u32(raw, 0x24),
        playback_value=u32(raw, 0x28),
        raw_2c=u32(raw, 0x2C),
        frame_or_sample_count=u32(raw, 0x30),
        raw_34=u32(raw, 0x34),
        trailing_parameters=u32(raw, 0x38),
        trailing_format=u32(raw, 0x3C),
        raw_40=u32(raw, 0x40),
    )


def parse_group(block: bytes, data_base: int, entry: DirectoryEntry) -> Group:
    start = data_base + entry.data_offset
    end = start + entry.byte_length
    if end > len(block):
        raise ValueError(
            f"{entry.bank} resource {entry.resource_id!r} exceeds the block"
        )

    zone_count = u32(block, start)
    header_size = u32(block, start + 4)
    expected_header_size = 8 + zone_count * 4
    expected_size = expected_header_size + zone_count * ZONE_SIZE
    if header_size != expected_header_size:
        raise ValueError(
            f"group at 0x{start:x}: header size 0x{header_size:x}, "
            f"expected 0x{expected_header_size:x}"
        )
    if entry.byte_length != expected_size:
        raise ValueError(
            f"group at 0x{start:x}: length 0x{entry.byte_length:x}, "
            f"expected 0x{expected_size:x}"
        )

    offsets = [u32(block, start + 8 + i * 4) for i in range(zone_count)]
    expected_offsets = [i * ZONE_SIZE for i in range(zone_count)]
    if offsets != expected_offsets:
        raise ValueError(
            f"group at 0x{start:x}: non-canonical zone offset table"
        )

    zones = [
        parse_zone(block, start + header_size + relative)
        for relative in offsets
    ]
    return Group(
        bank=entry.bank,
        resource_id=entry.resource_id,
        data_offset=entry.data_offset,
        byte_length=entry.byte_length,
        zone_count=zone_count,
        header_size=header_size,
        zone_offsets=offsets,
        zones=zones,
    )


def parse_number(value: str) -> int:
    return int(value, 0)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path, help="MBA/GAM containing the bank")
    parser.add_argument(
        "--file-offset",
        type=parse_number,
        required=True,
        help="bank start as a byte file offset (for G1: 0x6e46c)",
    )
    parser.add_argument(
        "--length",
        type=parse_number,
        required=True,
        help="bank length in bytes (for G1: 0x34b8)",
    )
    parser.add_argument("--output", type=Path, help="write full JSON report")
    args = parser.parse_args()

    image = args.image.read_bytes()
    if len(image) < 0x1000 or image[:8] != MAGIC:
        raise ValueError(f"{args.image}: not an MBA/GAM container")
    block = image[args.file_offset:args.file_offset + args.length]
    if len(block) != args.length:
        raise ValueError("requested bank range exceeds the image")

    (
        primary_count,
        primary,
        secondary_count,
        secondary,
        data_base,
    ) = parse_directory(block)
    entries = primary + secondary
    groups = [parse_group(block, data_base, entry) for entry in entries]
    zones = [zone for group in groups for zone in group.zones]

    expected_end = max(
        data_base + entry.data_offset + entry.byte_length for entry in entries
    )
    if expected_end != len(block):
        raise ValueError(
            f"directories end at 0x{expected_end:x}, block ends at "
            f"0x{len(block):x}"
        )

    tags = Counter(zone.tag for zone in zones)
    report = {
        "schema": 1,
        "classification": {
            "working_name": "SPF2ALP sound-patch bank",
            "confidence": "strong",
            "reason": (
                "zone records use key ranges and audio-like sample/playback "
                "fields; related firmware records contain 11025 Hz values"
            ),
            "copyright_note": (
                "metadata only; this report does not extract retail audio"
            ),
        },
        "source": {
            "path": str(args.image.resolve()),
            "sha256": hashlib.sha256(image).hexdigest(),
            "file_offset": args.file_offset,
            "byte_length": args.length,
            "block_sha256": hashlib.sha256(block).hexdigest(),
        },
        "layout": {
            "primary_group_count": primary_count,
            "secondary_group_count": secondary_count,
            "data_base": data_base,
            "zone_size": ZONE_SIZE,
            "group_size_formula": "8 + 4*zone_count + 0x44*zone_count",
            "parsed_end": expected_end,
        },
        "summary": {
            "group_count": len(groups),
            "zone_count": len(zones),
            "zones_per_group": dict(
                sorted(Counter(group.zone_count for group in groups).items())
            ),
            "tags": dict(sorted(tags.items())),
            "playback_values": sorted(set(zone.playback_value for zone in zones)),
            "signature_a_values": sorted(set(zone.signature_a for zone in zones)),
            "signature_b_values": sorted(set(zone.signature_b for zone in zones)),
        },
        "groups": [asdict(group) for group in groups],
    }

    encoded = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
