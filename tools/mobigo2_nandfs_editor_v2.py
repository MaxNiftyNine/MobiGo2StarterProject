#!/usr/bin/env python3
"""Read, extract, edit, and repack MOBIGOFS3.0 from a MobiGo 2 NAND dump.

This tool was derived from the supplied MobiGo 2 emulator and NAND image.
Write-back is deliberately conservative: it changes the contents and sizes of
existing files only, preserves the original NAND OOB bytes and block mapping,
and always writes a separate output image.

Raw NAND geometry used by the MobiGo 2 dump:
    2048 data bytes + 64 spare/OOB bytes per page
    64 pages per erase block

The NAND translation layer stores a logical erase-block number in OOB bytes
2..3.  After logical blocks are reordered, MOBIGOFS3.0 is exposed.  The file
system uses 16 KiB blocks, 8 KiB halves, and 512-byte records.  Each record has
4 wrapper bytes before and 4 wrapper/checksum bytes after 504 payload bytes.
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime as _datetime
import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path, PurePosixPath
import struct
import sys
from typing import Iterable, Iterator, Optional

PAGE_DATA = 2048
PAGE_OOB = 64
PAGE_RAW = PAGE_DATA + PAGE_OOB
PAGES_PER_ERASE_BLOCK = 64
ERASE_BLOCK_DATA = PAGE_DATA * PAGES_PER_ERASE_BLOCK  # 0x20000

FS_BLOCK = 0x4000
FS_HALF = 0x2000
RECORD = 0x200
RECORD_PAYLOAD = RECORD - 8  # 504 bytes
HALF_RECORDS = FS_HALF // RECORD
HALF_PAYLOAD = HALF_RECORDS * RECORD_PAYLOAD  # 8064 bytes
METADATA_BLOCKS = 0x20
FS_SIGNATURE = "MOBIGOFS3.0".encode("utf-16le")
EMPTY_ENTRY_CHECK = 0x000084F9
MANIFEST_NAME = ".mobigo2_manifest.json"


class FormatError(RuntimeError):
    """Raised when the input does not match the expected dump/filesystem format."""


@dataclasses.dataclass(frozen=True)
class Snapshot:
    base: int
    root_generation: int


@dataclasses.dataclass(frozen=True)
class DirEntry:
    name: str
    check: int
    target: int
    timestamp: int
    parent_path: PurePosixPath
    is_dir: bool

    @property
    def path(self) -> PurePosixPath:
        return self.parent_path / self.name

    @property
    def timestamp_text(self) -> str:
        if not self.timestamp:
            return "-"
        try:
            return _datetime.datetime.fromtimestamp(
                self.timestamp, _datetime.timezone.utc
            ).isoformat().replace("+00:00", "Z")
        except (OverflowError, OSError, ValueError):
            return f"0x{self.timestamp:08x}"


@dataclasses.dataclass(frozen=True)
class FileIndex:
    block: int
    size_words: int
    next_index: int
    data_blocks: tuple[int, ...]

    @property
    def size_bytes(self) -> int:
        return self.size_words * 2


class RawNand:
    def __init__(self, path: Path):
        self.path = path
        self.raw = path.read_bytes()
        if len(self.raw) % PAGE_RAW:
            raise FormatError(
                f"raw NAND size {len(self.raw)} is not a multiple of {PAGE_RAW}"
            )
        self.page_count = len(self.raw) // PAGE_RAW
        if self.page_count % PAGES_PER_ERASE_BLOCK:
            raise FormatError("raw NAND has a partial erase block")
        self.physical_block_count = self.page_count // PAGES_PER_ERASE_BLOCK
        self.mapping, self.mapping_warnings = self._build_mapping()
        self.logical = self._build_logical_image()

    def _page_data(self, page: int) -> bytes:
        off = page * PAGE_RAW
        return self.raw[off : off + PAGE_DATA]

    def _page_oob(self, page: int) -> bytes:
        off = page * PAGE_RAW + PAGE_DATA
        return self.raw[off : off + PAGE_OOB]

    def _build_mapping(self) -> tuple[dict[int, int], list[str]]:
        candidates: dict[int, list[tuple[int, int]]] = {}
        warnings: list[str] = []

        for physical in range(self.physical_block_count):
            first_page = physical * PAGES_PER_ERASE_BLOCK
            oob = self._page_oob(first_page)

            # OOB[0] is the conventional bad-block marker.  OOB[2:4] is the
            # logical erase-block number used by this MobiGo translation layer.
            if oob[0] != 0xFF or oob[2:4] == b"\xff\xff":
                continue
            logical = int.from_bytes(oob[2:4], "little")
            if logical >= self.physical_block_count:
                continue
            generation = oob[1]
            candidates.setdefault(logical, []).append((generation, physical))

        if not candidates or 0 not in candidates:
            raise FormatError("could not find MobiGo logical-block tags in NAND OOB")

        mapping: dict[int, int] = {}
        for logical, versions in candidates.items():
            # The supplied dump has one physical version per logical block.
            # Selecting the largest generation is a sensible read-only fallback
            # for dumps that retain an older physical copy.
            generation, physical = max(versions, key=lambda item: item[0])
            mapping[logical] = physical
            if len(versions) > 1:
                warnings.append(
                    f"logical block {logical:#x} has {len(versions)} versions; "
                    f"selected physical block {physical:#x} (generation {generation:#x})"
                )

        max_logical = max(mapping)
        missing = [n for n in range(max_logical + 1) if n not in mapping]
        if missing:
            warnings.append(
                f"{len(missing)} logical blocks are missing and will read as erased; "
                f"first missing block: {missing[0]:#x}"
            )
        return mapping, warnings

    def _build_logical_image(self) -> bytes:
        out = bytearray()
        erased = b"\xff" * PAGE_DATA
        max_logical = max(self.mapping)

        for logical in range(max_logical + 1):
            physical = self.mapping.get(logical)
            if physical is None:
                out.extend(erased * PAGES_PER_ERASE_BLOCK)
                continue

            pages: list[Optional[bytes]] = [None] * PAGES_PER_ERASE_BLOCK
            for physical_page_in_block in range(PAGES_PER_ERASE_BLOCK):
                page = physical * PAGES_PER_ERASE_BLOCK + physical_page_in_block
                oob = self._page_oob(page)
                tagged_page = int.from_bytes(oob[6:8], "little")

                # On translated blocks the optional page tag agrees with the
                # physical page index.  Honor it when valid; otherwise preserve
                # physical order.  All-zero boot OOB is deliberately ignored.
                if (
                    oob[:12] != b"\x00" * 12
                    and tagged_page != 0xFFFF
                    and tagged_page < PAGES_PER_ERASE_BLOCK
                ):
                    destination = tagged_page
                else:
                    destination = physical_page_in_block
                pages[destination] = self._page_data(page)

            for page in pages:
                out.extend(page if page is not None else erased)
        return bytes(out)


class MobigoFS:
    def __init__(self, nand: RawNand, fs_base: Optional[int] = None):
        self.nand = nand
        self.image = nand.logical
        self.snapshots = self._find_snapshots()
        if not self.snapshots:
            raise FormatError("MOBIGOFS3.0 signature not found in translated NAND")

        if fs_base is None:
            self.snapshot = max(self.snapshots, key=lambda s: s.root_generation)
        else:
            matches = [s for s in self.snapshots if s.base == fs_base]
            if not matches:
                known = ", ".join(f"0x{s.base:x}" for s in self.snapshots)
                raise FormatError(f"filesystem base 0x{fs_base:x} not found; candidates: {known}")
            self.snapshot = matches[0]

        self._directory_cache: dict[int, list[DirEntry]] = {}
        self.root_entries = self._read_directory(2, PurePosixPath("/"))
        self.entries: dict[str, DirEntry] = {}
        self._walk(2, PurePosixPath("/"), set())

    def _find_snapshots(self) -> list[Snapshot]:
        found: list[Snapshot] = []
        start = 0
        while True:
            pos = self.image.find(FS_SIGNATURE, start)
            if pos < 0:
                break
            base = pos - 4
            start = pos + 1
            if base < 0 or base % FS_BLOCK:
                continue
            root = base + 2 * FS_BLOCK
            if root + FS_HALF > len(self.image):
                continue
            generation = struct.unpack_from("<I", self.image, root)[0]
            if generation >= 0x10000:
                continue
            found.append(Snapshot(base=base, root_generation=generation))
        return found

    @staticmethod
    def _decode_name(raw: bytes) -> str:
        if len(raw) != 12:
            raise ValueError("MobiGo names are exactly 12 packed bytes")
        swapped = bytearray()
        for i in range(0, len(raw), 2):
            swapped.extend((raw[i + 1], raw[i]))
        encoded = bytes(swapped).split(b"\0", 1)[0]
        return encoded.decode("latin-1", errors="replace").strip()

    def _half_payload(self, offset: int) -> bytes:
        if offset < 0 or offset + FS_HALF > len(self.image):
            raise FormatError(f"filesystem half at 0x{offset:x} is outside translated image")
        out = bytearray()
        for record_off in range(offset, offset + FS_HALF, RECORD):
            out.extend(self.image[record_off + 4 : record_off + RECORD - 4])
        return bytes(out)

    def _directory_half(self, block: int) -> tuple[int, int]:
        base_offset = self.snapshot.base + block * FS_BLOCK
        choices: list[tuple[int, int]] = []
        for half_offset in (base_offset, base_offset + FS_HALF):
            if half_offset + FS_HALF > len(self.image):
                continue
            generation = struct.unpack_from("<I", self.image, half_offset)[0]
            if generation < 0x10000:
                choices.append((generation, half_offset))
        if not choices:
            raise FormatError(f"directory block {block:#x} has no valid metadata half")
        return max(choices, key=lambda item: item[0])

    def _read_directory(self, block: int, parent_path: PurePosixPath) -> list[DirEntry]:
        cache_key = (self.snapshot.base << 16) ^ block
        if cache_key in self._directory_cache:
            # Paths are assigned while walking, so cached entries are safe only
            # for the one canonical parent in this tree.
            return self._directory_cache[cache_key]

        _generation, half_offset = self._directory_half(block)
        entries: list[DirEntry] = []

        for record_index in range(HALF_RECORDS):
            record_off = half_offset + record_index * RECORD
            payload = self.image[record_off + 4 : record_off + RECORD - 4]
            # Four bytes of per-record directory metadata precede 20 entries.
            for slot in range(20):
                off = 4 + slot * 24
                item = payload[off : off + 24]
                if len(item) < 24:
                    continue
                raw_name = item[:12]
                check, target, timestamp = struct.unpack_from("<III", item, 12)
                if raw_name == b"\0" * 12:
                    continue
                name = self._decode_name(raw_name)
                if not name:
                    continue

                is_dir = target < METADATA_BLOCKS
                entries.append(
                    DirEntry(
                        name=name,
                        check=check,
                        target=target,
                        timestamp=timestamp,
                        parent_path=parent_path,
                        is_dir=is_dir,
                    )
                )

        self._directory_cache[cache_key] = entries
        return entries

    def _walk(self, block: int, path: PurePosixPath, seen: set[int]) -> None:
        if block in seen:
            raise FormatError(f"directory cycle detected at metadata block {block:#x}")
        seen.add(block)
        for entry in self._read_directory(block, path):
            key = self._normalize(entry.path)
            self.entries[key] = entry
            if entry.is_dir:
                self._walk(entry.target, entry.path, seen)
        seen.remove(block)

    @staticmethod
    def _normalize(path: str | PurePosixPath) -> str:
        p = PurePosixPath(path)
        text = "/" + str(p).lstrip("/")
        return text.rstrip("/") or "/"

    def get(self, path: str) -> Optional[DirEntry]:
        normalized = self._normalize(path)
        if normalized == "/":
            return None
        direct = self.entries.get(normalized)
        if direct is not None:
            return direct
        # MobiGo lookup is effectively case-insensitive for these packed names.
        folded = normalized.casefold()
        for candidate, entry in self.entries.items():
            if candidate.casefold() == folded:
                return entry
        raise FileNotFoundError(path)

    def children(self, path: str = "/") -> list[DirEntry]:
        normalized = self._normalize(path)
        if normalized == "/":
            block = 2
            parent = PurePosixPath("/")
        else:
            entry = self.get(normalized)
            if entry is None or not entry.is_dir:
                raise NotADirectoryError(path)
            block = entry.target
            parent = entry.path
        return sorted(self._read_directory(block, parent), key=lambda e: (not e.is_dir, e.name.casefold()))

    def _read_index(self, block: int) -> FileIndex:
        offset = block * FS_BLOCK
        if offset + FS_BLOCK > len(self.image):
            raise FormatError(f"file-index block {block:#x} is outside translated image")

        size_words = 0
        next_index = 0
        data_blocks: list[int] = []
        for sector in range(HALF_RECORDS):
            record_off = offset + sector * RECORD
            payload = self.image[record_off + 4 : record_off + RECORD - 4]
            values = struct.unpack("<" + "I" * (len(payload) // 4), payload)
            if sector == 0:
                size_words, next_index = values[0], values[1]
                candidates = values[2:]
            else:
                # First word is a continuation/reserved field.
                candidates = values[1:]
            for value in candidates:
                if value == 0:
                    break
                if value * FS_BLOCK >= len(self.image):
                    raise FormatError(
                        f"file-index block {block:#x} references invalid data block {value:#x}"
                    )
                data_blocks.append(value)

        if size_words * 2 > len(self.image) * 4:
            raise FormatError(f"implausible file size in index block {block:#x}: {size_words:#x} words")
        return FileIndex(block, size_words, next_index, tuple(data_blocks))

    def read_file(self, entry_or_path: DirEntry | str) -> bytes:
        entry = entry_or_path if isinstance(entry_or_path, DirEntry) else self.get(entry_or_path)
        if entry is None or entry.is_dir:
            raise IsADirectoryError(str(entry_or_path))

        output = bytearray()
        index_block = entry.target
        seen: set[int] = set()
        expected_size: Optional[int] = None

        while index_block:
            if index_block in seen:
                raise FormatError(f"file-index cycle at block {index_block:#x}")
            seen.add(index_block)
            index = self._read_index(index_block)
            if expected_size is None:
                expected_size = index.size_bytes
            elif index.size_bytes not in (0, expected_size):
                raise FormatError("inconsistent size in chained file-index blocks")

            # The second half of every index block is the first data chunk for
            # that allocation extent.
            output.extend(self._half_payload(index_block * FS_BLOCK + FS_HALF))
            for data_block in index.data_blocks:
                block_offset = data_block * FS_BLOCK
                output.extend(self._half_payload(block_offset))
                output.extend(self._half_payload(block_offset + FS_HALF))
            index_block = index.next_index

        assert expected_size is not None
        if len(output) < expected_size:
            raise FormatError(
                f"file {entry.path} is truncated: recovered {len(output)} of {expected_size} bytes"
            )
        return bytes(output[:expected_size])

    def iter_tree(self) -> Iterator[tuple[int, DirEntry]]:
        def recurse(path: str, depth: int) -> Iterator[tuple[int, DirEntry]]:
            for child in self.children(path):
                yield depth, child
                if child.is_dir:
                    yield from recurse(str(child.path), depth + 1)
        yield from recurse("/", 0)


def parse_int(value: str) -> int:
    return int(value, 0)


def safe_output_path(root: Path, internal: PurePosixPath) -> Path:
    parts = [part for part in internal.parts if part not in ("/", "", ".", "..")]
    candidate = root.joinpath(*parts)
    root_resolved = root.resolve()
    parent_resolved = candidate.parent.resolve()
    if root_resolved != parent_resolved and root_resolved not in parent_resolved.parents:
        raise FormatError(f"unsafe internal path: {internal}")
    return candidate


def cmd_info(fs: MobigoFS) -> None:
    nand = fs.nand
    print(f"Raw image:              {nand.path}")
    print(f"Raw bytes:              {len(nand.raw)}")
    print(f"Physical pages:         {nand.page_count}")
    print(f"Physical erase blocks:  {nand.physical_block_count}")
    print(f"Mapped logical blocks:  {len(nand.mapping)} (0..{max(nand.mapping)})")
    print(f"Translated bytes:       {len(nand.logical)}")
    print("Filesystem snapshots:")
    for snap in fs.snapshots:
        marker = " *" if snap == fs.snapshot else ""
        print(f"  base=0x{snap.base:08x} root_generation={snap.root_generation}{marker}")
    files = sum(1 for e in fs.entries.values() if not e.is_dir)
    directories = sum(1 for e in fs.entries.values() if e.is_dir)
    print(f"Directories:            {directories}")
    print(f"Files:                  {files}")
    for warning in nand.mapping_warnings:
        print(f"Warning: {warning}", file=sys.stderr)


def print_entries(entries: Iterable[DirEntry], fs: MobigoFS, long: bool = False) -> None:
    for entry in entries:
        kind = "d" if entry.is_dir else "f"
        if long and not entry.is_dir:
            index = fs._read_index(entry.target)
            size = index.size_bytes
        else:
            size = 0
        if long:
            print(
                f"{kind} {size:10d} check={entry.check:08x} "
                f"time={entry.timestamp_text:20s} {entry.name}"
            )
        else:
            suffix = "/" if entry.is_dir else ""
            print(entry.name + suffix)


def cmd_ls(fs: MobigoFS, path: str, long: bool) -> None:
    entry = fs.get(path)
    if entry is not None and not entry.is_dir:
        print_entries([entry], fs, long)
    else:
        print_entries(fs.children(path), fs, long)


def cmd_tree(fs: MobigoFS, long: bool) -> None:
    print("/")
    for depth, entry in fs.iter_tree():
        prefix = "    " * depth + "- "
        if long and not entry.is_dir:
            size = fs._read_index(entry.target).size_bytes
            print(f"{prefix}{entry.name} ({size} bytes)")
        else:
            print(prefix + entry.name + ("/" if entry.is_dir else ""))


def cmd_cat(fs: MobigoFS, path: str) -> None:
    sys.stdout.buffer.write(fs.read_file(path))


def cmd_extract(fs: MobigoFS, path: str, output: Path) -> None:
    data = fs.read_file(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(data)
    print(f"Extracted {len(data)} bytes to {output}")


def cmd_extract_all(fs: MobigoFS, output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    count = 0
    total = 0
    for _depth, entry in fs.iter_tree():
        destination = safe_output_path(output, entry.path)
        if entry.is_dir:
            destination.mkdir(parents=True, exist_ok=True)
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        data = fs.read_file(entry)
        destination.write_bytes(data)
        if entry.timestamp:
            try:
                os.utime(destination, (entry.timestamp, entry.timestamp))
            except (OSError, OverflowError):
                pass
        print(f"{entry.path} -> {destination} ({len(data)} bytes)")
        count += 1
        total += len(data)
    print(f"Extracted {count} files, {total} bytes total")


def cmd_dump_logical(fs: MobigoFS, output: Path) -> None:
    output.write_bytes(fs.nand.logical)
    print(f"Wrote {len(fs.nand.logical)} translated bytes to {output}")


def _file_layout(fs: MobigoFS, entry: DirEntry) -> tuple[list[FileIndex], list[int]]:
    """Return index records and ordered 8 KiB storage-half offsets for a file."""
    indexes: list[FileIndex] = []
    halves: list[int] = []
    index_block = entry.target
    seen: set[int] = set()
    while index_block:
        if index_block in seen:
            raise FormatError(f"file-index cycle at block {index_block:#x}")
        seen.add(index_block)
        index = fs._read_index(index_block)
        indexes.append(index)
        halves.append(index.block * FS_BLOCK + FS_HALF)
        for data_block in index.data_blocks:
            halves.append(data_block * FS_BLOCK)
            halves.append(data_block * FS_BLOCK + FS_HALF)
        index_block = index.next_index
    return indexes, halves


def _record_checksum(record: bytes | bytearray | memoryview) -> int:
    """MOBIGOFS record checksum: additive sum of the first 255 LE words."""
    if len(record) != RECORD:
        raise ValueError("record must be exactly 512 bytes")
    return sum(struct.unpack_from("<255H", record, 0)) & 0xFFFF


def _refresh_record(image: bytearray, record_offset: int) -> None:
    # Trailer bytes 508..509 mirror the record's first two bytes.  The final
    # word is an additive checksum over bytes 0..509.
    image[record_offset + RECORD - 4 : record_offset + RECORD - 2] = image[
        record_offset : record_offset + 2
    ]
    record = memoryview(image)[record_offset : record_offset + RECORD]
    struct.pack_into("<H", image, record_offset + RECORD - 2, _record_checksum(record))


def _write_half_payload(image: bytearray, half_offset: int, payload: bytes) -> None:
    if len(payload) != HALF_PAYLOAD:
        raise ValueError(f"half payload must be {HALF_PAYLOAD} bytes")
    if half_offset < 0 or half_offset + FS_HALF > len(image):
        raise FormatError(f"storage half at 0x{half_offset:x} is outside translated image")
    cursor = 0
    for sector in range(HALF_RECORDS):
        record_offset = half_offset + sector * RECORD
        image[record_offset + 4 : record_offset + RECORD - 4] = payload[
            cursor : cursor + RECORD_PAYLOAD
        ]
        cursor += RECORD_PAYLOAD
        _refresh_record(image, record_offset)


def _write_file_to_logical(
    fs: MobigoFS, image: bytearray, entry: DirEntry, data: bytes
) -> int:
    if len(data) & 1:
        raise FormatError(
            f"{entry.path}: size {len(data)} is odd; MOBIGOFS stores file sizes in 16-bit words"
        )
    indexes, halves = _file_layout(fs, entry)
    capacity = len(halves) * HALF_PAYLOAD
    if len(data) > capacity:
        raise FormatError(
            f"{entry.path}: {len(data)} bytes exceeds its existing allocation of "
            f"{capacity} bytes (over by {len(data) - capacity} bytes)"
        )

    padded = data + b"\xff" * (capacity - len(data))
    cursor = 0
    for half_offset in halves:
        _write_half_payload(image, half_offset, padded[cursor : cursor + HALF_PAYLOAD])
        cursor += HALF_PAYLOAD

    size_words = len(data) // 2
    for number, index in enumerate(indexes):
        # The first index contains the size.  Chained indexes sometimes repeat
        # it and sometimes store zero, so preserve zero continuation fields.
        if number == 0 or index.size_words != 0:
            record_offset = index.block * FS_BLOCK
            struct.pack_into("<I", image, record_offset + 4, size_words)
            _refresh_record(image, record_offset)
    return capacity


def _logical_to_raw(nand: RawNand, logical_image: bytes | bytearray) -> bytes:
    if len(logical_image) != len(nand.logical):
        raise FormatError("translated image size changed unexpectedly")
    raw = bytearray(nand.raw)
    for logical_block, physical_block in nand.mapping.items():
        for physical_page_in_block in range(PAGES_PER_ERASE_BLOCK):
            raw_page = physical_block * PAGES_PER_ERASE_BLOCK + physical_page_in_block
            oob = nand._page_oob(raw_page)
            tagged_page = int.from_bytes(oob[6:8], "little")
            if (
                oob[:12] != b"\x00" * 12
                and tagged_page != 0xFFFF
                and tagged_page < PAGES_PER_ERASE_BLOCK
            ):
                logical_page_in_block = tagged_page
            else:
                logical_page_in_block = physical_page_in_block
            logical_page = logical_block * PAGES_PER_ERASE_BLOCK + logical_page_in_block
            source = logical_page * PAGE_DATA
            destination = raw_page * PAGE_RAW
            raw[destination : destination + PAGE_DATA] = logical_image[
                source : source + PAGE_DATA
            ]
    return bytes(raw)


def _relative_path(internal: PurePosixPath) -> Path:
    return Path(*[part for part in internal.parts if part not in ("/", "", ".", "..")])


def _is_ignored_host_path(relative: Path) -> bool:
    return any(
        part == MANIFEST_NAME
        or part == ".DS_Store"
        or part == "__MACOSX"
        or part.startswith("._")
        for part in relative.parts
    )


def _expected_tree(fs: MobigoFS) -> tuple[dict[Path, DirEntry], set[Path]]:
    files: dict[Path, DirEntry] = {}
    directories: set[Path] = set()
    for _depth, entry in fs.iter_tree():
        relative = _relative_path(entry.path)
        if entry.is_dir:
            directories.add(relative)
        else:
            files[relative] = entry
            directories.update(relative.parents)
    directories.discard(Path("."))
    return files, directories


def _scan_host_tree(folder: Path) -> tuple[set[Path], set[Path]]:
    files: set[Path] = set()
    directories: set[Path] = set()
    for root, dirnames, filenames in os.walk(folder, followlinks=False):
        root_path = Path(root)
        relative_root = root_path.relative_to(folder)
        kept_dirs: list[str] = []
        for name in dirnames:
            relative = relative_root / name
            path = root_path / name
            if _is_ignored_host_path(relative):
                continue
            if path.is_symlink():
                raise FormatError(f"symbolic links are not supported: {path}")
            directories.add(relative)
            kept_dirs.append(name)
        dirnames[:] = kept_dirs
        for name in filenames:
            relative = relative_root / name
            path = root_path / name
            if _is_ignored_host_path(relative):
                continue
            if path.is_symlink():
                raise FormatError(f"symbolic links are not supported: {path}")
            files.add(relative)
    return files, directories


def _validate_edit_folder(fs: MobigoFS, folder: Path) -> dict[Path, DirEntry]:
    if not folder.is_dir():
        raise FileNotFoundError(f"edit folder does not exist: {folder}")
    expected_files, expected_directories = _expected_tree(fs)
    actual_files, actual_directories = _scan_host_tree(folder)

    missing_files = sorted(expected_files.keys() - actual_files)
    extra_files = sorted(actual_files - expected_files.keys())
    missing_directories = sorted(expected_directories - actual_directories)
    extra_directories = sorted(actual_directories - expected_directories)
    problems: list[str] = []
    if missing_files:
        problems.append("missing files: " + ", ".join(map(str, missing_files[:8])))
    if extra_files:
        problems.append("added/renamed files: " + ", ".join(map(str, extra_files[:8])))
    if missing_directories:
        problems.append("missing directories: " + ", ".join(map(str, missing_directories[:8])))
    if extra_directories:
        problems.append("added/renamed directories: " + ", ".join(map(str, extra_directories[:8])))
    if problems:
        raise FormatError(
            "the folder structure no longer matches the NAND filesystem; "
            "adding, deleting, or renaming entries is not supported:\n  "
            + "\n  ".join(problems)
        )
    return expected_files


def _manifest(fs: MobigoFS) -> dict[str, object]:
    files: list[dict[str, object]] = []
    for _depth, entry in fs.iter_tree():
        if entry.is_dir:
            continue
        _indexes, halves = _file_layout(fs, entry)
        files.append(
            {
                "path": str(entry.path),
                "size": fs._read_index(entry.target).size_bytes,
                "capacity": len(halves) * HALF_PAYLOAD,
            }
        )
    return {
        "format": "MOBIGOFS3.0 edit folder",
        "source_nand": str(fs.nand.path),
        "source_sha256": hashlib.sha256(fs.nand.raw).hexdigest(),
        "filesystem_base": f"0x{fs.snapshot.base:x}",
        "files": files,
    }


def _extract_edit_folder(fs: MobigoFS, folder: Path, overwrite: bool) -> None:
    if folder.exists() and any(folder.iterdir()):
        if not overwrite:
            raise FormatError(
                f"edit folder is not empty: {folder}; choose a new folder or use --overwrite-folder"
            )
        shutil.rmtree(folder)
    cmd_extract_all(fs, folder)
    manifest_path = folder / MANIFEST_NAME
    manifest_path.write_text(json.dumps(_manifest(fs), indent=2) + "\n", encoding="utf-8")
    print(f"Wrote edit manifest to {manifest_path}")


def _verify_repacked(
    original_fs: MobigoFS, output_path: Path, expected: dict[str, bytes]
) -> None:
    rebuilt_nand = RawNand(output_path)
    rebuilt_fs = MobigoFS(rebuilt_nand, original_fs.snapshot.base)
    rebuilt_paths = {
        str(entry.path)
        for _depth, entry in rebuilt_fs.iter_tree()
        if not entry.is_dir
    }
    if rebuilt_paths != set(expected):
        raise FormatError("verification failed: rebuilt filesystem tree changed")
    for internal_path, wanted in expected.items():
        actual = rebuilt_fs.read_file(internal_path)
        if actual != wanted:
            raise FormatError(f"verification failed: contents differ for {internal_path}")

    # OOB must remain bit-for-bit identical.  This editor intentionally does
    # not regenerate physical NAND ECC and is intended for the emulator.
    for page in range(original_fs.nand.page_count):
        if original_fs.nand._page_oob(page) != rebuilt_nand._page_oob(page):
            raise FormatError(f"verification failed: OOB changed on physical page {page:#x}")


def cmd_repack_folder(fs: MobigoFS, folder: Path, output: Path) -> None:
    source_resolved = fs.nand.path.resolve()
    output_resolved = output.resolve()
    if source_resolved == output_resolved:
        raise FormatError("refusing to overwrite the source NAND; choose a different output file")

    expected_files = _validate_edit_folder(fs, folder)
    logical = bytearray(fs.image)
    verification_data: dict[str, bytes] = {}
    changed: list[tuple[str, int, int, int]] = []

    for relative, entry in sorted(expected_files.items(), key=lambda item: str(item[0])):
        host_path = folder / relative
        data = host_path.read_bytes()
        old = fs.read_file(entry)
        _indexes, halves = _file_layout(fs, entry)
        capacity = len(halves) * HALF_PAYLOAD
        if len(data) & 1:
            raise FormatError(
                f"{entry.path}: size {len(data)} is odd; add one padding byte before repacking"
            )
        if len(data) > capacity:
            raise FormatError(
                f"{entry.path}: {len(data)} bytes exceeds its allocation of {capacity} bytes"
            )
        verification_data[str(entry.path)] = data
        if data != old:
            _write_file_to_logical(fs, logical, entry, data)
            changed.append((str(entry.path), len(old), len(data), capacity))

    output.parent.mkdir(parents=True, exist_ok=True)
    raw_output = _logical_to_raw(fs.nand, logical)
    temporary: Optional[Path] = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", prefix=output.name + ".", suffix=".tmp", dir=output.parent, delete=False
        ) as handle:
            temporary = Path(handle.name)
            handle.write(raw_output)
            handle.flush()
            os.fsync(handle.fileno())
        _verify_repacked(fs, temporary, verification_data)
        os.replace(temporary, output)
        temporary = None
    finally:
        if temporary is not None:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass

    if changed:
        print("Changed files:")
        for path, old_size, new_size, capacity in changed:
            print(f"  {path}: {old_size} -> {new_size} bytes (capacity {capacity})")
    else:
        print("No file contents changed; wrote a verified copy of the NAND.")
    print(f"Wrote and verified new NAND image: {output} ({len(raw_output)} bytes)")
    print("The original NAND was not modified.")


def cmd_edit_folder(
    fs: MobigoFS, folder: Path, output: Path, overwrite_folder: bool
) -> None:
    _extract_edit_folder(fs, folder, overwrite_folder)
    print("\nEdit the extracted files now.")
    print("Supported: replacing or resizing existing file contents.")
    print("Not supported: adding, deleting, or renaming files/directories.")
    print("Files must have an even byte size and fit their existing allocation.")
    try:
        input("\nPress Enter when you are ready to build the new NAND image...")
    except EOFError as exc:
        raise FormatError(
            "standard input closed before Enter was pressed; use repack-folder later"
        ) from exc
    cmd_repack_folder(fs, folder, output)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("nand", type=Path, help="raw NAND dump including 64-byte OOB per page")
    parser.add_argument(
        "--fs-base",
        type=parse_int,
        help="force a MOBIGOFS snapshot base (for example 0x80000); auto-selects newest by default",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("info", help="show NAND mapping and filesystem information")

    p_ls = sub.add_parser("ls", help="list a directory or file")
    p_ls.add_argument("path", nargs="?", default="/")
    p_ls.add_argument("-l", "--long", action="store_true")

    p_tree = sub.add_parser("tree", help="print the complete directory tree")
    p_tree.add_argument("-l", "--long", action="store_true")

    p_cat = sub.add_parser("cat", help="write one file to standard output")
    p_cat.add_argument("path")

    p_extract = sub.add_parser("extract", help="extract one file")
    p_extract.add_argument("path")
    p_extract.add_argument("output", type=Path)

    p_all = sub.add_parser("extract-all", help="extract the complete filesystem")
    p_all.add_argument("output", type=Path)

    p_logical = sub.add_parser("dump-logical", help="write the translated logical-block image")
    p_logical.add_argument("output", type=Path)

    p_edit = sub.add_parser(
        "edit-folder",
        help="extract to a folder, wait for Enter, then build and verify a new NAND",
    )
    p_edit.add_argument("folder", type=Path, help="working folder to create")
    p_edit.add_argument("output", type=Path, help="new raw NAND image to write")
    p_edit.add_argument(
        "--overwrite-folder",
        action="store_true",
        help="delete and recreate a non-empty working folder",
    )

    p_repack = sub.add_parser(
        "repack-folder",
        help="build and verify a new NAND from a previously extracted folder",
    )
    p_repack.add_argument("folder", type=Path)
    p_repack.add_argument("output", type=Path)
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        nand = RawNand(args.nand)
        fs = MobigoFS(nand, args.fs_base)
        if args.command == "info":
            cmd_info(fs)
        elif args.command == "ls":
            cmd_ls(fs, args.path, args.long)
        elif args.command == "tree":
            cmd_tree(fs, args.long)
        elif args.command == "cat":
            cmd_cat(fs, args.path)
        elif args.command == "extract":
            cmd_extract(fs, args.path, args.output)
        elif args.command == "extract-all":
            cmd_extract_all(fs, args.output)
        elif args.command == "dump-logical":
            cmd_dump_logical(fs, args.output)
        elif args.command == "edit-folder":
            cmd_edit_folder(fs, args.folder, args.output, args.overwrite_folder)
        elif args.command == "repack-folder":
            cmd_repack_folder(fs, args.folder, args.output)
        else:
            raise AssertionError(args.command)
        return 0
    except (FormatError, FileNotFoundError, NotADirectoryError, IsADirectoryError, PermissionError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
