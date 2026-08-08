#!/usr/bin/env python3
"""Build the Homebrew Launcher as a donor-free SY MBA."""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir", type=Path, default=Path("build/homebrew-launcher")
    )
    args = parser.parse_args()
    here = Path(__file__).resolve().parent
    root = here.parents[1]
    output = args.output_dir.resolve()
    generated = output / "generated_wave"
    subprocess.run(
        [sys.executable, str(here / "generate_wave_bundle.py"), str(generated)],
        check=True,
    )
    subprocess.run(
        [
            sys.executable,
            str(root / "tools/build/build_sdk_app.py"),
            str(here / "main.c"),
            "--output-dir", str(output),
            "--slot", "SY",
            "--name", "HomebrewLauncher",
            "--with-clean-font",
            "--extra-source", str(generated / "hb_wave_resources.c"),
        ],
        check=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

