#!/usr/bin/env python3
"""Locate statically linked functions after relocation or minor recompilation.

The tool votes on short exact instruction-word anchors and then scores each
candidate by aligned 16-bit-word equality.  It is intentionally a locator, not
proof of semantic identity: candidates must still be checked in Ghidra.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from array import array
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path


MAGIC = b"bM_gbMQa"
HEADER_WORDS = 0x800


@dataclass(frozen=True)
class Image:
    path: str
    name: str
    sha256: str
    runtime_base: int
    body_load: int
    entry: int
    words: array


@dataclass(frozen=True)
class FunctionSpec:
    name: str
    start: int
    end_exclusive: int


@dataclass(frozen=True)
class Candidate:
    target_runtime_address: int
    target_file_offset: int
    anchor_votes: int
    equal_words: int
    function_words: int
    aligned_equality: float
    longest_equal_run_words: int


def load_image(path: Path) -> Image:
    data = path.read_bytes()
    if len(data) < 0x1000 or len(data) & 1 or data[:8] != MAGIC:
        raise ValueError(f"{path}: not a valid even-sized MBA/GAM")
    _, _, _, entry, body_load = struct.unpack_from("<5I", data, 8)
    words = array("H")
    words.frombytes(data)
    if struct.pack("=H", 1) != struct.pack("<H", 1):
        words.byteswap()
    return Image(
        path=str(path.resolve()),
        name=path.name,
        sha256=hashlib.sha256(data).hexdigest(),
        runtime_base=body_load - HEADER_WORDS,
        body_load=body_load,
        entry=entry,
        words=words,
    )


def parse_int(text: str) -> int:
    return int(text, 0)


def parse_function(text: str) -> FunctionSpec:
    try:
        name, start, end = text.split(":", 2)
    except ValueError as error:
        raise argparse.ArgumentTypeError(
            "function must be NAME:START:END_EXCLUSIVE"
        ) from error
    try:
        result = FunctionSpec(name, parse_int(start), parse_int(end))
    except ValueError as error:
        raise argparse.ArgumentTypeError(str(error)) from error
    if not name or result.end_exclusive <= result.start:
        raise argparse.ArgumentTypeError("invalid function name or range")
    return result


def longest_equal_run(reference: array, target: array) -> int:
    longest = 0
    current = 0
    for left, right in zip(reference, target):
        if left == right:
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return longest


def target_anchor_index(
    words: array,
    anchor_words: int,
    maximum_occurrences: int,
    wanted: set[tuple[int, ...]],
) -> dict[tuple[int, ...], list[int]]:
    index: defaultdict[tuple[int, ...], list[int]] = defaultdict(list)
    for position in range(HEADER_WORDS, len(words) - anchor_words + 1):
        key = tuple(words[position:position + anchor_words])
        if key not in wanted:
            continue
        positions = index[key]
        if len(positions) <= maximum_occurrences:
            positions.append(position)
    return {
        key: positions
        for key, positions in index.items()
        if len(positions) <= maximum_occurrences
    }


def locate(
    reference: Image,
    target: Image,
    spec: FunctionSpec,
    *,
    anchor_words: int,
    maximum_occurrences: int,
    candidates: int,
    target_index: dict[tuple[int, ...], list[int]],
) -> list[Candidate]:
    reference_start = spec.start - reference.runtime_base
    reference_end = spec.end_exclusive - reference.runtime_base
    if reference_start < HEADER_WORDS or reference_end > len(reference.words):
        raise ValueError(f"{spec.name}: range is outside the reference body")
    function = reference.words[reference_start:reference_end]

    votes: Counter[int] = Counter()
    for relative in range(len(function) - anchor_words + 1):
        key = tuple(function[relative:relative + anchor_words])
        for target_anchor in target_index.get(key, ()):
            candidate_start = target_anchor - relative
            if (
                candidate_start >= HEADER_WORDS
                and candidate_start + len(function) <= len(target.words)
            ):
                votes[candidate_start] += 1

    result = []
    for target_start, anchor_votes in votes.most_common(candidates * 8):
        target_words = target.words[target_start:target_start + len(function)]
        equal = sum(left == right for left, right in zip(function, target_words))
        result.append(
            Candidate(
                target_runtime_address=target.runtime_base + target_start,
                target_file_offset=target_start * 2,
                anchor_votes=anchor_votes,
                equal_words=equal,
                function_words=len(function),
                aligned_equality=round(equal / len(function), 6),
                longest_equal_run_words=longest_equal_run(function, target_words),
            )
        )

    result.sort(
        key=lambda item: (
            item.anchor_votes,
            item.equal_words,
            item.longest_equal_run_words,
        ),
        reverse=True,
    )
    return result[:candidates]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", type=Path)
    parser.add_argument("targets", type=Path, nargs="+")
    parser.add_argument(
        "--function",
        type=parse_function,
        action="append",
        required=True,
        help="NAME:START:END_EXCLUSIVE in runtime word addresses",
    )
    parser.add_argument("--anchor-words", type=int, default=6)
    parser.add_argument("--maximum-occurrences", type=int, default=8)
    parser.add_argument("--candidates", type=int, default=3)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if min(args.anchor_words, args.maximum_occurrences, args.candidates) <= 0:
        parser.error("anchor, occurrence, and candidate counts must be positive")

    reference = load_image(args.reference)
    wanted_anchors: set[tuple[int, ...]] = set()
    for spec in args.function:
        start = spec.start - reference.runtime_base
        end = spec.end_exclusive - reference.runtime_base
        if start < HEADER_WORDS or end > len(reference.words):
            raise ValueError(f"{spec.name}: range is outside the reference body")
        function = reference.words[start:end]
        wanted_anchors.update(
            tuple(function[position:position + args.anchor_words])
            for position in range(len(function) - args.anchor_words + 1)
        )

    report = {
        "schema": 1,
        "warning": (
            "Candidates are similarity leads and require Ghidra verification; "
            "aligned equality can understate matches with inserted instructions"
        ),
        "algorithm": {
            "anchor_words": args.anchor_words,
            "maximum_anchor_occurrences": args.maximum_occurrences,
            "reported_candidates": args.candidates,
        },
        "reference": {
            key: value
            for key, value in asdict(reference).items()
            if key != "words"
        },
        "functions": [asdict(spec) for spec in args.function],
        "targets": [],
    }

    for target_path in args.targets:
        target = load_image(target_path)
        index = target_anchor_index(
            target.words,
            args.anchor_words,
            args.maximum_occurrences,
            wanted_anchors,
        )
        target_report = {
            "image": {
                key: value
                for key, value in asdict(target).items()
                if key != "words"
            },
            "matches": {},
        }
        for spec in args.function:
            target_report["matches"][spec.name] = [
                asdict(candidate)
                for candidate in locate(
                    reference,
                    target,
                    spec,
                    anchor_words=args.anchor_words,
                    maximum_occurrences=args.maximum_occurrences,
                    candidates=args.candidates,
                    target_index=index,
                )
            ]
        report["targets"].append(target_report)

    encoded = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
