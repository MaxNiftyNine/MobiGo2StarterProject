#!/usr/bin/env python3
"""Read and write the Homebrew Launcher INDEX.HB catalog."""

from __future__ import annotations

from dataclasses import dataclass
import argparse
from pathlib import Path
import struct


MAGIC = b"HB01"
HEADER_SIZE = 8
PATH_BYTES = 42
LABEL_BYTES = 20
ENTRY_SIZE = 64
MAX_ENTRIES = 16


@dataclass(frozen=True)
class CatalogEntry:
    path: str
    label: str
    flags: int = 0


def _ascii_field(value: str, size: int, field: str) -> bytes:
    try:
        encoded = value.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError(f"{field} must contain ASCII characters") from exc
    if not encoded or len(encoded) >= size:
        raise ValueError(f"{field} must be 1 to {size - 1} ASCII bytes")
    return encoded.ljust(size, b"\0")


def encode_catalog(entries: list[CatalogEntry]) -> bytes:
    if len(entries) > MAX_ENTRIES:
        raise ValueError(f"catalog supports at most {MAX_ENTRIES} entries")
    output = bytearray(MAGIC + struct.pack("<HH", len(entries), ENTRY_SIZE))
    for entry in entries:
        output += _ascii_field(entry.path, PATH_BYTES, "path")
        output += _ascii_field(entry.label, LABEL_BYTES, "label")
        output += struct.pack("<H", entry.flags & 0xFFFF)
    return bytes(output)


def decode_catalog(data: bytes) -> list[CatalogEntry]:
    if len(data) < HEADER_SIZE or data[:4] != MAGIC:
        raise ValueError("not a Homebrew Launcher catalog")
    count, entry_size = struct.unpack_from("<HH", data, 4)
    if count > MAX_ENTRIES or entry_size != ENTRY_SIZE:
        raise ValueError("unsupported Homebrew Launcher catalog layout")
    expected = HEADER_SIZE + count * ENTRY_SIZE
    if len(data) < expected:
        raise ValueError("truncated Homebrew Launcher catalog")
    entries: list[CatalogEntry] = []
    for index in range(count):
        offset = HEADER_SIZE + index * ENTRY_SIZE
        path = data[offset : offset + PATH_BYTES].split(b"\0", 1)[0]
        label = data[offset + PATH_BYTES : offset + PATH_BYTES + LABEL_BYTES]
        flags = struct.unpack_from("<H", data, offset + PATH_BYTES + LABEL_BYTES)[0]
        entries.append(
            CatalogEntry(
                path.decode("ascii"),
                label.split(b"\0", 1)[0].decode("ascii"),
                flags,
            )
        )
    return entries


def write_catalog(path: Path, entries: list[CatalogEntry]) -> None:
    path.write_bytes(encode_catalog(entries))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create an INDEX.HB catalog while preserving .MBA filenames."
    )
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--entry",
        nargs=2,
        action="append",
        metavar=("PATH", "LABEL"),
        default=[],
        help=r"add one target path and display label, for example A:\HB\Pong.MBA Pong.MBA",
    )
    args = parser.parse_args()
    write_catalog(
        args.output,
        [CatalogEntry(path, label) for path, label in args.entry],
    )
    print(f"Wrote {len(args.entry)} entries to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
