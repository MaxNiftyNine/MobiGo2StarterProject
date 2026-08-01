#!/usr/bin/env python3
"""Reassemble the GitHub-safe pieces of the US stitched MobiGo 2 NAND dump."""

from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import sys


EXPECTED_SIZE = 138_412_032
EXPECTED_SHA256 = "66e686225f709e07ca0d76b78b82374cb6fd27296c7a3d8b98c765da66442e7a"
PART_NAMES = ("nand.us-stitched.bin.part00", "nand.us-stitched.bin.part01")
CHUNK_SIZE = 1024 * 1024


def hash_file(path: Path) -> tuple[int, str]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as source:
        while chunk := source.read(CHUNK_SIZE):
            size += len(chunk)
            digest.update(chunk)
    return size, digest.hexdigest()


def valid_image(path: Path) -> bool:
    if not path.is_file():
        return False
    size, digest = hash_file(path)
    return size == EXPECTED_SIZE and digest == EXPECTED_SHA256


def assemble(output: Path, parts_dir: Path) -> None:
    parts = [parts_dir / name for name in PART_NAMES]
    missing = [str(part) for part in parts if not part.is_file()]
    if missing:
        raise RuntimeError("missing NAND part(s): " + ", ".join(missing))

    temporary = output.with_name(output.name + ".tmp")
    if temporary.exists():
        raise RuntimeError(f"temporary output already exists: {temporary}")

    digest = hashlib.sha256()
    size = 0
    try:
        with temporary.open("xb") as destination:
            for part in parts:
                with part.open("rb") as source:
                    while chunk := source.read(CHUNK_SIZE):
                        destination.write(chunk)
                        digest.update(chunk)
                        size += len(chunk)
        if size != EXPECTED_SIZE or digest.hexdigest() != EXPECTED_SHA256:
            raise RuntimeError(
                "reassembled NAND verification failed: "
                f"size={size} sha256={digest.hexdigest()}"
            )
        os.replace(temporary, output)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parents[2]
        / "vendor"
        / "firmware"
        / "nand.us-stitched.bin",
        help="path of the reassembled NAND image",
    )
    parser.add_argument(
        "--parts-dir",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "vendor" / "firmware",
        help="directory containing the numbered NAND parts",
    )
    args = parser.parse_args()

    if valid_image(args.output):
        print(f"PASS NAND already assembled and verified: {args.output}")
        return 0
    if args.output.exists():
        parser.error(f"existing NAND does not match the expected image: {args.output}")

    try:
        assemble(args.output, args.parts_dir)
    except RuntimeError as error:
        parser.error(str(error))
    print(f"PASS assembled and verified NAND: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
