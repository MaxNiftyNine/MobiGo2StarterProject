#!/usr/bin/env python3
"""Extract the region-specific G1 or SY donor MBA from a raw MobiGo NAND."""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent


def load_editor(path: Path):
    spec = importlib.util.spec_from_file_location("slot_nand_editor", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import NAND editor: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("nand", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--slot", choices=("G1", "SY"), default="SY")
    parser.add_argument(
        "--editor", type=Path, default=HERE / "mobigo2_nandfs_editor_v2.py"
    )
    args = parser.parse_args()

    editor = load_editor(args.editor.expanduser().resolve())
    nand = editor.RawNand(args.nand.expanduser().resolve())
    fs = editor.MobigoFS(nand)
    directory = f"/BUNDLE/{args.slot}"
    suffix = f"{args.slot}.MBA"
    matches = [
        entry
        for entry in fs.children(directory)
        if not entry.is_dir and entry.name.upper().endswith(suffix)
    ]
    if len(matches) != 1:
        raise RuntimeError(
            f"expected one *{suffix} in {directory}, found {len(matches)}"
        )
    data = fs.read_file(str(matches[0].path))
    output = args.output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(data)
    print(f"PASS extracted {matches[0].path} ({len(data)} bytes) to {output}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"extract_slot_mba: {exc}", file=sys.stderr)
        raise SystemExit(1)
