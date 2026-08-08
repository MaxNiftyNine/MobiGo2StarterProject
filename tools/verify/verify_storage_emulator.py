#!/usr/bin/env python3
"""Verify the recovered resident storage API against the retail firmware backend."""

from __future__ import annotations

import shutil
import struct
import subprocess
import sys
from pathlib import Path

from emulator_support import find_emulator, mba_overlay_arguments


def read_word(data: bytes, base: int, address: int) -> int:
    return struct.unpack_from("<H", data, (address - base) * 2)[0]


def read_u32(data: bytes, base: int, address: int) -> int:
    return read_word(data, base, address) | (read_word(data, base, address + 1) << 16)


def build_and_run(root: Path, source: Path, name: str, dump_base: int, dump_words: int) -> bytes:
    starter = root
    build = root / "build" / name
    emulator = find_emulator(starter)
    if build.exists():
        shutil.rmtree(build)

    subprocess.run(
        [
            sys.executable,
            str(root / "tools" / "build" / "build_sdk_app.py"),
            str(source),
            "--output-dir", str(build),
            "--name", name,
            "--slot", "SY",
        ],
        check=True,
    )

    ram = build / "storage_ram.bin"
    subprocess.run(
        [
            str(emulator),
            "--rom", str(starter / "vendor" / "firmware" / "internalrom.bin"),
            "--spi", str(starter / "vendor" / "firmware" / "spi.bin"),
            *mba_overlay_arguments(root, build / f"{name}.MBA"),
            "--no-window",
            "--steps", "225000000",
            "--dump-memory", str(ram),
            "--dump-memory-base", hex(dump_base),
            "--dump-memory-words", hex(dump_words),
        ],
        check=True,
    )
    return ram.read_bytes()


def verify_read(root: Path) -> None:
    base = 0x5940
    data = build_and_run(
        root,
        root / "examples" / "storage_read_boot_test.c",
        "StorageReadCheck",
        base,
        0x40,
    )
    status = read_word(data, base, base + 0)
    handle = read_word(data, base, base + 1)
    size = read_u32(data, base, base + 2)
    first_read = read_u32(data, base, base + 4)
    first_match = read_word(data, base, base + 6)
    seek = read_word(data, base, base + 7)
    tail_read = read_u32(data, base, base + 8)
    tail_match = read_word(data, base, base + 10)
    close = read_word(data, base, base + 11)
    exists = read_word(data, base, base + 12)

    expected = {
        "status": (status, 0x7101),
        "size": (size, 38),
        "first_read": (first_read, 8),
        "first_match": (first_match, 1),
        "seek": (seek, 0),
        "tail_read": (tail_read, 6),
        "tail_match": (tail_match, 1),
        "close": (close, 0),
        "exists": (exists, 1),
    }
    for label, (actual, wanted) in expected.items():
        if actual != wanted:
            raise SystemExit(f"FAIL storage-read {label}={actual:#x}, expected {wanted:#x}")
    if handle == 0xFFFF:
        raise SystemExit("FAIL storage-read returned invalid handle")
    print(
        "PASS storage-read "
        f"status={status:#06x} handle={handle:#06x} size={size} "
        f"first={first_read} seek={seek} tail={tail_read} close={close}"
    )


def verify_overwrite(root: Path) -> None:
    base = 0x5900
    data = build_and_run(
        root,
        root / "examples" / "storage_boot_test.c",
        "StorageOverwriteCheck",
        base,
        0x50,
    )
    status = read_word(data, base, base + 0)
    exists_before = read_word(data, base, base + 1)
    write_handle = read_word(data, base, base + 2)
    written = read_u32(data, base, base + 3)
    write_size = read_u32(data, base, base + 5)
    close_write = read_word(data, base, base + 7)
    exists_after = read_word(data, base, base + 8)
    read_handle = read_word(data, base, base + 9)
    read_size = read_u32(data, base, base + 10)
    read_amount = read_u32(data, base, base + 12)
    match = read_word(data, base, base + 14)
    seek = read_word(data, base, base + 15)
    tail_amount = read_u32(data, base, base + 16)
    tail_match = read_word(data, base, base + 18)
    close_read = read_word(data, base, base + 19)
    truncate = read_word(data, base, base + 20)

    expected = {
        "status": (status, 0x7001),
        "exists_before": (exists_before, 1),
        "written": (written, 8),
        "write_size": (write_size, 8),
        "close_write": (close_write, 0),
        "exists_after": (exists_after, 1),
        "read_size": (read_size, 8),
        "read_amount": (read_amount, 8),
        "match": (match, 1),
        "seek": (seek, 0),
        "tail_amount": (tail_amount, 4),
        "tail_match": (tail_match, 1),
        "close_read": (close_read, 0),
        "truncate": (truncate, 0),
    }
    for label, (actual, wanted) in expected.items():
        if actual != wanted:
            raise SystemExit(f"FAIL storage-overwrite {label}={actual:#x}, expected {wanted:#x}")
    if write_handle == 0xFFFF or read_handle == 0xFFFF:
        raise SystemExit("FAIL storage-overwrite returned invalid handle")
    if write_handle == read_handle:
        raise SystemExit("FAIL storage-overwrite handle generation did not advance")
    print(
        "PASS storage-overwrite "
        f"status={status:#06x} handles={write_handle:#06x}->{read_handle:#06x} "
        f"written={written} size={read_size} tail={tail_amount}"
    )


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    verify_read(root)
    verify_overwrite(root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
