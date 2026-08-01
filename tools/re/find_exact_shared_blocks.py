#!/usr/bin/env python3
"""Find long exact word sequences shared by MBA/GAM containers.

The matcher uses verified 16-bit word addressing, ignores the 0x1000-byte
container header, and reports both file offsets and mapped runtime addresses.
It is intended to identify strong candidates for statically linked common code
or shared data before semantic Ghidra comparison.

Exact equality is deliberately a high-confidence but incomplete signal:
relocation, different compiler options, and patched constants can make common
source code differ at the binary level.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from array import array
from dataclasses import asdict, dataclass
from pathlib import Path


MAGIC = b"bM_gbMQa"
HEADER_WORDS = 0x800
MASK64 = (1 << 64) - 1
ROLL_BASE = 0x100000001B3


@dataclass(frozen=True)
class ImageInfo:
    path: str
    name: str
    sha256: str
    size_bytes: int
    size_words: int
    runtime_base: int
    body_load: int
    entry: int
    title: str


@dataclass(frozen=True)
class Match:
    reference_word_offset: int
    target_word_offset: int
    length_words: int
    reference_file_offset: int
    target_file_offset: int
    reference_runtime_address: int
    target_runtime_address: int
    same_runtime_address: bool


def load_image(path: Path) -> tuple[ImageInfo, array]:
    data = path.read_bytes()
    if len(data) < 0x1000 or len(data) & 1 or data[:8] != MAGIC:
        raise ValueError(f"{path}: not a valid even-sized MBA/GAM container")

    size_words, _, _, entry, body_load = struct.unpack_from("<5I", data, 0x08)
    if size_words * 2 != len(data):
        raise ValueError(f"{path}: declared size does not match file length")

    title_bytes = data[0x80:0xA0].split(b"\0", 1)[0]
    title = title_bytes.decode("ascii", errors="replace")
    words = array("H")
    words.frombytes(data)
    if sys.byteorder != "little":
        words.byteswap()

    info = ImageInfo(
        path=str(path.resolve()),
        name=path.name,
        sha256=hashlib.sha256(data).hexdigest(),
        size_bytes=len(data),
        size_words=size_words,
        runtime_base=body_load - HEADER_WORDS,
        body_load=body_load,
        entry=entry,
        title=title,
    )
    return info, words


def rolling_hashes(words: array, start: int, window: int):
    """Yield (position, hash) for every window beginning at or after start."""
    end = len(words) - window
    if start > end:
        return

    power = pow(ROLL_BASE, window - 1, 1 << 64)
    value = 0
    for word in words[start:start + window]:
        value = ((value * ROLL_BASE) + word + 1) & MASK64
    yield start, value

    for position in range(start + 1, end + 1):
        outgoing = words[position - 1] + 1
        incoming = words[position + window - 1] + 1
        value = (value - outgoing * power) & MASK64
        value = ((value * ROLL_BASE) + incoming) & MASK64
        yield position, value


def unique_anchor_index(words: array, start: int, window: int) -> dict[int, int]:
    """Map each unique nontrivial rolling hash to its word position.

    Repeated anchors are removed rather than expanded into potentially huge
    lists. Long common-library matches almost always contain at least one
    unique anchor; omitting repetitive bitmap/zero-fill anchors keeps memory
    bounded and prevents meaningless matches.
    """
    index: dict[int, int] = {}
    repeated: set[int] = set()
    for position, value in rolling_hashes(words, start, window):
        if value in repeated:
            continue
        previous = index.pop(value, None)
        if previous is None:
            index[value] = position
        else:
            repeated.add(value)
    return index


def extend_match(
    reference: array,
    target: array,
    ref_position: int,
    target_position: int,
    window: int,
    minimum_start: int,
) -> tuple[int, int, int]:
    if reference[ref_position:ref_position + window] != target[
        target_position:target_position + window
    ]:
        return ref_position, target_position, 0

    left = 0
    while (
        ref_position - left > minimum_start
        and target_position - left > minimum_start
        and reference[ref_position - left - 1] == target[target_position - left - 1]
    ):
        left += 1

    right = window
    while (
        ref_position + right < len(reference)
        and target_position + right < len(target)
        and reference[ref_position + right] == target[target_position + right]
    ):
        right += 1

    return ref_position - left, target_position - left, left + right


def find_matches(
    reference: array,
    target: array,
    *,
    anchor_words: int,
    anchor_stride: int,
    minimum_words: int,
) -> list[tuple[int, int, int]]:
    target_index = unique_anchor_index(target, HEADER_WORDS, anchor_words)
    matches: list[tuple[int, int, int]] = []
    covered_until = HEADER_WORDS

    reference_hashes = rolling_hashes(reference, HEADER_WORDS, anchor_words)
    for ref_position, value in reference_hashes:
        if (ref_position - HEADER_WORDS) % anchor_stride:
            continue
        if ref_position < covered_until:
            continue
        target_position = target_index.get(value)
        if target_position is None:
            continue

        ref_start, target_start, length = extend_match(
            reference,
            target,
            ref_position,
            target_position,
            anchor_words,
            HEADER_WORDS,
        )
        if length < minimum_words:
            continue
        matches.append((ref_start, target_start, length))
        covered_until = ref_start + length

    return matches


def describe_matches(
    reference_info: ImageInfo,
    target_info: ImageInfo,
    raw_matches: list[tuple[int, int, int]],
) -> list[Match]:
    result = []
    for ref_word, target_word, length in raw_matches:
        ref_address = reference_info.runtime_base + ref_word
        target_address = target_info.runtime_base + target_word
        result.append(
            Match(
                reference_word_offset=ref_word,
                target_word_offset=target_word,
                length_words=length,
                reference_file_offset=ref_word * 2,
                target_file_offset=target_word * 2,
                reference_runtime_address=ref_address,
                target_runtime_address=target_address,
                same_runtime_address=ref_address == target_address,
            )
        )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", type=Path)
    parser.add_argument("targets", type=Path, nargs="+")
    parser.add_argument(
        "--anchor-words",
        type=int,
        default=32,
        help="rolling-hash anchor size in 16-bit words (default: 32)",
    )
    parser.add_argument(
        "--anchor-stride",
        type=int,
        default=8,
        help="sample every Nth reference anchor (default: 8)",
    )
    parser.add_argument(
        "--minimum-words",
        type=int,
        default=64,
        help="minimum reported exact match in 16-bit words (default: 64)",
    )
    parser.add_argument("--output", type=Path, help="write complete JSON report")
    args = parser.parse_args()

    if min(args.anchor_words, args.anchor_stride, args.minimum_words) <= 0:
        parser.error("anchor and minimum sizes must be positive")
    if args.minimum_words < args.anchor_words + args.anchor_stride - 1:
        parser.error(
            "minimum match must be at least anchor_words + anchor_stride - 1 "
            "to guarantee a sampled anchor"
        )

    reference_info, reference_words = load_image(args.reference)
    report = {
        "schema": 1,
        "units": "16-bit words unless field name says bytes",
        "algorithm": {
            "kind": "exact rolling-hash anchors with byte-for-byte verification",
            "anchor_words": args.anchor_words,
            "anchor_stride": args.anchor_stride,
            "minimum_words": args.minimum_words,
            "header_words_ignored": HEADER_WORDS,
        },
        "reference": asdict(reference_info),
        "comparisons": [],
    }

    print(
        f"reference {reference_info.name}: {reference_info.size_bytes:#x} bytes, "
        f"base={reference_info.runtime_base:#x}, entry={reference_info.entry:#x}"
    )
    for target_path in args.targets:
        target_info, target_words = load_image(target_path)
        raw = find_matches(
            reference_words,
            target_words,
            anchor_words=args.anchor_words,
            anchor_stride=args.anchor_stride,
            minimum_words=args.minimum_words,
        )
        matches = describe_matches(reference_info, target_info, raw)
        shared_words = sum(item.length_words for item in matches)
        same_address_words = sum(
            item.length_words for item in matches if item.same_runtime_address
        )
        comparison = {
            "target": asdict(target_info),
            "shared_words": shared_words,
            "shared_bytes": shared_words * 2,
            "same_runtime_address_words": same_address_words,
            "matches": [asdict(item) for item in matches],
        }
        report["comparisons"].append(comparison)

        print(
            f"{target_info.name}: matches={len(matches)} "
            f"shared={shared_words * 2:#x} bytes "
            f"same-address={same_address_words * 2:#x} bytes"
        )
        for item in sorted(matches, key=lambda match: match.length_words, reverse=True)[:8]:
            print(
                f"  {item.length_words * 2:#8x} bytes "
                f"G1 {item.reference_runtime_address:#08x} -> "
                f"{target_info.title or target_info.name} "
                f"{item.target_runtime_address:#08x}"
                f"{' SAME' if item.same_runtime_address else ''}"
            )

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
