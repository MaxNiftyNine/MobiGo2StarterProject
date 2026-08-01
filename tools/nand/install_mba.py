#!/usr/bin/env python3
"""Install an MBA into every selected G1 or SY slot in a raw MobiGo NAND image.

The input image is never modified. The result is written to a separate path
and read back through the filesystem parser before the command succeeds.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import os
import struct
import sys
import tempfile
from pathlib import Path


HERE = Path(__file__).resolve().parent


def load_editor(editor_path: Path):
    if not editor_path.is_file():
        raise RuntimeError(
            f"required NAND filesystem module is missing: {editor_path}"
        )
    spec = importlib.util.spec_from_file_location("mba_nand_editor", editor_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {editor_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def erased_physical_blocks(editor, nand) -> list[int]:
    used = set(nand.mapping.values())
    result: list[int] = []
    for physical in range(nand.physical_block_count - 1, -1, -1):
        if physical in used:
            continue
        first_oob = nand._page_oob(physical * editor.PAGES_PER_ERASE_BLOCK)
        if first_oob[0] != 0xFF or first_oob[2:4] != b"\xff\xff":
            continue
        if all(
            nand._page_data(physical * editor.PAGES_PER_ERASE_BLOCK + page)
            == b"\xff" * editor.PAGE_DATA
            for page in range(editor.PAGES_PER_ERASE_BLOCK)
        ):
            result.append(physical)
    return result


def add_logical_blocks(editor, nand, count: int, temporary_dir: Path):
    if count == 0:
        return nand, []
    physicals = erased_physical_blocks(editor, nand)[:count]
    if len(physicals) != count:
        raise RuntimeError(f"need {count} erased NAND blocks, found {len(physicals)}")
    first_logical = max(nand.mapping) + 1
    if first_logical + count > nand.physical_block_count:
        raise RuntimeError("not enough logical block numbers remain")
    raw = bytearray(nand.raw)
    added: list[tuple[int, int]] = []
    for number, physical in enumerate(physicals):
        logical = first_logical + number
        for page in range(editor.PAGES_PER_ERASE_BLOCK):
            raw_page = physical * editor.PAGES_PER_ERASE_BLOCK + page
            oob = raw_page * editor.PAGE_RAW + editor.PAGE_DATA
            raw[oob + 1] = 1
            struct.pack_into("<H", raw, oob + 2, logical)
        added.append((logical, physical))
    expanded_path = temporary_dir / "expanded.raw"
    expanded_path.write_bytes(raw)
    return editor.RawNand(expanded_path), added


def write_index(editor, logical: bytearray, index_block: int,
                size: int, blocks: list[int]) -> None:
    slots: list[int] = []
    for sector in range(editor.HALF_RECORDS):
        record = index_block * editor.FS_BLOCK + sector * editor.RECORD
        payload = record + 4
        start = 8 if sector == 0 else 4
        slots.extend(range(payload + start, payload + editor.RECORD_PAYLOAD, 4))
    if len(blocks) >= len(slots):
        raise RuntimeError("MBA is too large for one MOBIGOFS file index")
    for offset in slots:
        struct.pack_into("<I", logical, offset, 0)
    for offset, block in zip(slots, blocks):
        struct.pack_into("<I", logical, offset, block)
    struct.pack_into("<I", logical, index_block * editor.FS_BLOCK + 4, size // 2)
    struct.pack_into("<I", logical, index_block * editor.FS_BLOCK + 8, 0)
    for sector in range(editor.HALF_RECORDS):
        editor._refresh_record(
            logical, index_block * editor.FS_BLOCK + sector * editor.RECORD
        )


def initialize_half(editor, logical: bytearray,
                    half_offset: int, half_number: int) -> None:
    for record in range(editor.HALF_RECORDS):
        group = half_number * 4 + record // 4 + 1
        struct.pack_into(
            "<HH", logical, half_offset + record * editor.RECORD, group, 1
        )


def write_expanded_file(editor, fs, logical: bytearray,
                        entry, data: bytes, new_blocks: list[int]) -> None:
    index = fs._read_index(entry.target)
    if index.next_index:
        raise RuntimeError("chained file indexes are not supported")
    blocks = list(index.data_blocks) + new_blocks
    write_index(editor, logical, entry.target, len(data), blocks)
    halves = [entry.target * editor.FS_BLOCK + editor.FS_HALF]
    for block in blocks:
        halves.extend((block * editor.FS_BLOCK, block * editor.FS_BLOCK + editor.FS_HALF))
    capacity = len(halves) * editor.HALF_PAYLOAD
    if len(data) > capacity:
        raise RuntimeError("expanded MBA allocation is unexpectedly too small")
    padded = data + b"\xff" * (capacity - len(data))
    first_new_half = 1 + len(index.data_blocks) * 2
    for half_number, half_offset in enumerate(halves):
        if half_number >= first_new_half:
            initialize_half(editor, logical, half_offset, half_number)
        start = half_number * editor.HALF_PAYLOAD
        editor._write_half_payload(
            logical, half_offset, padded[start:start + editor.HALF_PAYLOAD]
        )


def slot_files(editor, nand, slot: str) -> list[tuple[int, str, int]]:
    result: list[tuple[int, str, int]] = []
    directory = f"/BUNDLE/{slot}"
    suffix = f"{slot}.MBA"
    snapshots = sorted(editor.MobigoFS(nand).snapshots, key=lambda item: item.base)
    for snapshot in snapshots:
        fs = editor.MobigoFS(nand, snapshot.base)
        try:
            children = fs.children(directory)
        except FileNotFoundError:
            continue
        candidates = [entry for entry in children
                      if not entry.is_dir and entry.name.upper().endswith(suffix)]
        if not candidates:
            continue
        if len(candidates) != 1:
            raise RuntimeError(
                f"snapshot {snapshot.base:#x}: expected one {slot} MBA, "
                f"found {len(candidates)}"
            )
        entry = candidates[0]
        result.append((snapshot.base, str(entry.path), entry.target))
    if not result:
        raise RuntimeError(f"no {directory}/*{suffix} file was found")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Install an MBA into all selected G1 or SY copies in a raw NAND image"
    )
    parser.add_argument("--slot", choices=("G1", "SY"), default="G1")
    parser.add_argument("nand", type=Path, help="source raw NAND image")
    parser.add_argument("mba", type=Path, help="MBA file to install in the selected slot")
    parser.add_argument("output", type=Path, help="new raw NAND image to write")
    parser.add_argument(
        "--editor",
        type=Path,
        default=HERE / "mobigo2_nandfs_editor_v2.py",
        help="path to mobigo2_nandfs_editor_v2.py (default: beside this script)",
    )
    args = parser.parse_args()

    source_nand = args.nand.expanduser().resolve()
    mba_path = args.mba.expanduser().resolve()
    output_nand = args.output.expanduser().resolve()
    editor_path = args.editor.expanduser().resolve()
    if not mba_path.is_file():
        parser.error(f"MBA file does not exist: {mba_path}")
    if not source_nand.is_file():
        parser.error(f"source NAND does not exist: {source_nand}")
    if source_nand == output_nand:
        parser.error("output must be different from the source NAND")
    data = mba_path.read_bytes()
    if not data:
        parser.error("MBA file is empty")
    if len(data) & 1:
        parser.error("MBA size is odd; MOBIGOFS stores sizes in 16-bit words")

    editor = load_editor(editor_path)
    source = editor.RawNand(source_nand)
    original_hash = hashlib.sha256(source.raw).hexdigest()
    targets = slot_files(editor, source, args.slot)

    unique_targets = sorted({target for _base, _path, target in targets})
    existing_fs = editor.MobigoFS(source)
    extra_per_target: dict[int, int] = {}
    total_extra = 0
    for target in unique_targets:
        index = existing_fs._read_index(target)
        capacity = (1 + len(index.data_blocks) * 2) * editor.HALF_PAYLOAD
        extra = 0
        while capacity + extra * 2 * editor.HALF_PAYLOAD < len(data):
            extra += 1
        extra_per_target[target] = extra
        total_extra += extra

    logical_blocks_needed = (total_extra + 7) // 8
    output_nand.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output_nand.parent) as temporary_name:
        temporary_dir = Path(temporary_name)
        expanded, added = add_logical_blocks(
            editor, source, logical_blocks_needed, temporary_dir
        )
        logical = bytearray(expanded.logical)
        free_fs_blocks = [logical_block * 8 + within
                          for logical_block, _physical in added
                          for within in range(8)]
        allocation_cursor = 0
        expanded_fs = editor.MobigoFS(expanded)
        for target in unique_targets:
            entry = next(
                editor.MobigoFS(expanded, base).get(path)
                for base, path, candidate_target in targets
                if candidate_target == target
            )
            extra_count = extra_per_target[target]
            allocated = free_fs_blocks[
                allocation_cursor:allocation_cursor + extra_count
            ]
            allocation_cursor += extra_count
            if extra_count:
                write_expanded_file(
                    editor, expanded_fs, logical, entry, data, allocated
                )
            else:
                editor._write_file_to_logical(
                    expanded_fs, logical, entry, data
                )

        raw_output = editor._logical_to_raw(expanded, logical)
        verification_path = temporary_dir / "nand.edited.verify.bin"
        verification_path.write_bytes(raw_output)
        verification_nand = editor.RawNand(verification_path)
        for base, path, _target in targets:
            actual = editor.MobigoFS(verification_nand, base).read_file(path)
            if actual != data:
                raise RuntimeError(f"read-back verification failed: {path}")

        with tempfile.NamedTemporaryFile(
            mode="wb", dir=output_nand.parent,
            prefix=output_nand.name + ".", suffix=".tmp", delete=False
        ) as handle:
            temporary_output = Path(handle.name)
            handle.write(raw_output)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_output, output_nand)

    if hashlib.sha256(source_nand.read_bytes()).hexdigest() != original_hash:
        raise RuntimeError("source NAND changed unexpectedly")
    installed = ", ".join(sorted({path for _base, path, _target in targets}))
    print(f"PASS installed {mba_path} ({len(data)} bytes) as {installed}")
    print(f"PASS verified all {len(targets)} filesystem snapshot entries")
    print(f"PASS source NAND unchanged: {source_nand}")
    print(f"Wrote {output_nand}")
    print(f"SHA-256 {hashlib.sha256(output_nand.read_bytes()).hexdigest()}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1)
