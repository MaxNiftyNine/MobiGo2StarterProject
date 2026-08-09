#!/usr/bin/env python3
"""Read and write the Homebrew Launcher INDEX.HB catalog."""

from __future__ import annotations

from dataclasses import dataclass
import argparse
from pathlib import Path
import struct


MAGIC = b"HB02"
LEGACY_MAGIC = b"HB01"
HEADER_SIZE = 8
PATH_BYTES = 42
TITLE_BYTES = 18
DESCRIPTION_BYTES = 22
AUTHOR_BYTES = 10
ENTRY_SIZE = 96
LEGACY_LABEL_BYTES = 20
LEGACY_ENTRY_SIZE = 64
MAX_ENTRIES = 16

ICON_NAMES = ("default", "game", "puzzle", "media", "tool", "system")
ICON_IDS = {name: index for index, name in enumerate(ICON_NAMES)}


@dataclass(frozen=True)
class CatalogEntry:
    path: str
    title: str
    description: str = ""
    author: str = ""
    icon: int = 0
    flags: int = 0

    @property
    def label(self) -> str:
        """Compatibility name used by the first catalog revision."""
        return self.title


def icon_id(value: str | int) -> int:
    if isinstance(value, int):
        result = value
    else:
        try:
            result = ICON_IDS[value.strip().lower()]
        except KeyError as error:
            raise ValueError(f"icon must be one of: {', '.join(ICON_NAMES)}") from error
    if result < 0 or result >= len(ICON_NAMES):
        raise ValueError(f"icon id must be in range 0..{len(ICON_NAMES) - 1}")
    return result


def _ascii_field(value: str, size: int, field: str, *, required: bool) -> bytes:
    try:
        encoded = value.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError(f"{field} must contain ASCII characters") from exc
    minimum = 1 if required else 0
    if len(encoded) < minimum or len(encoded) >= size:
        qualifier = f"{minimum} to {size - 1}"
        raise ValueError(f"{field} must be {qualifier} ASCII bytes")
    return encoded.ljust(size, b"\0")


def encode_catalog(entries: list[CatalogEntry]) -> bytes:
    if len(entries) > MAX_ENTRIES:
        raise ValueError(f"catalog supports at most {MAX_ENTRIES} entries")
    output = bytearray(MAGIC + struct.pack("<HH", len(entries), ENTRY_SIZE))
    for entry in entries:
        output += _ascii_field(entry.path, PATH_BYTES, "path", required=True)
        output += _ascii_field(entry.title, TITLE_BYTES, "title", required=True)
        output += _ascii_field(
            entry.description, DESCRIPTION_BYTES, "description", required=False
        )
        output += _ascii_field(entry.author, AUTHOR_BYTES, "author", required=False)
        output += struct.pack(
            "<HH", icon_id(entry.icon), entry.flags & 0xFFFF
        )
    return bytes(output)


def _text(data: bytes) -> str:
    return data.split(b"\0", 1)[0].decode("ascii")


def decode_catalog(data: bytes) -> list[CatalogEntry]:
    if len(data) < HEADER_SIZE or data[:4] not in (MAGIC, LEGACY_MAGIC):
        raise ValueError("not a Homebrew Launcher catalog")
    count, entry_size = struct.unpack_from("<HH", data, 4)
    legacy = data[:4] == LEGACY_MAGIC
    expected_stride = LEGACY_ENTRY_SIZE if legacy else ENTRY_SIZE
    if count > MAX_ENTRIES or entry_size != expected_stride:
        raise ValueError("unsupported Homebrew Launcher catalog layout")
    expected = HEADER_SIZE + count * entry_size
    if len(data) < expected:
        raise ValueError("truncated Homebrew Launcher catalog")
    entries: list[CatalogEntry] = []
    for index in range(count):
        offset = HEADER_SIZE + index * entry_size
        path = _text(data[offset : offset + PATH_BYTES])
        if legacy:
            title = _text(
                data[offset + PATH_BYTES : offset + PATH_BYTES + LEGACY_LABEL_BYTES]
            )
            flags = struct.unpack_from("<H", data, offset + 62)[0]
            entries.append(CatalogEntry(path, title, flags=flags))
            continue
        title_at = offset + PATH_BYTES
        description_at = title_at + TITLE_BYTES
        author_at = description_at + DESCRIPTION_BYTES
        icon, flags = struct.unpack_from("<HH", data, author_at + AUTHOR_BYTES)
        entries.append(
            CatalogEntry(
                path,
                _text(data[title_at : title_at + TITLE_BYTES]),
                _text(data[description_at : description_at + DESCRIPTION_BYTES]),
                _text(data[author_at : author_at + AUTHOR_BYTES]),
                icon_id(icon),
                flags,
            )
        )
    return entries


def write_catalog(path: Path, entries: list[CatalogEntry]) -> None:
    path.write_bytes(encode_catalog(entries))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create an INDEX.HB catalog with launcher metadata."
    )
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--entry",
        nargs=2,
        action="append",
        metavar=("PATH", "TITLE"),
        default=[],
    )
    args = parser.parse_args()
    write_catalog(
        args.output,
        [CatalogEntry(path, title) for path, title in args.entry],
    )
    print(f"Wrote {len(args.entry)} entries to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
