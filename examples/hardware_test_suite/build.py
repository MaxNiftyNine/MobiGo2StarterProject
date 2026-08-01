#!/usr/bin/env python3
"""Build the complete real-hardware SDK diagnostic MBA."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def run(command: list[str]) -> None:
    subprocess.run(command, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("build/hardware-suite"))
    parser.add_argument("--slot", choices=("SY",), default="SY")
    parser.add_argument("--install-nand", action="store_true")
    args = parser.parse_args()

    here = Path(__file__).resolve().parent
    root = here.parents[1]
    output = args.output_dir.resolve()
    primary = output / "generated_primary"
    animation = output / "generated_animation"

    run([sys.executable, str(here / "generate_primary_bundle.py"), str(primary)])
    run([
        sys.executable,
        str(root / "tools/assets/build_family_b_animation_bundle.py"),
        str(animation),
        "--prefix",
        "hw_animation",
    ])

    command = [
        sys.executable,
        str(root / "tools/build/build_sdk_app.py"),
        str(here / "main.c"),
        "--output-dir",
        str(output),
        "--name",
        "MobiGo2HardwareSuite",
        "--slot",
        args.slot,
        "--without-system-ui",
        "--with-clean-font",
        "--extra-source",
        str(here / "self_tests.c"),
        "--extra-source",
        str(primary / "hw_primary_resources.c"),
        "--extra-source",
        str(animation / "hw_animation_resources.c"),
    ]
    if args.install_nand:
        command.append("--install-nand")
    run(command)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
