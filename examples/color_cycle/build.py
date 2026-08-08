#!/usr/bin/env python3
"""Build the color-cycle sample as a donor-free system-slot MBA."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("build/color-cycle"))
    parser.add_argument("--install-nand", action="store_true")
    args = parser.parse_args()

    here = Path(__file__).resolve().parent
    root = here.parents[1]
    command = [
        sys.executable,
        str(root / "tools/build/build_sdk_app.py"),
        str(here / "main.c"),
        "--output-dir",
        str(args.output_dir.resolve()),
        "--slot",
        "SY",
        "--name",
        "ColorCycle",
        "--without-system-ui",
    ]
    if args.install_nand:
        command.append("--install-nand")
    subprocess.run(command, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
