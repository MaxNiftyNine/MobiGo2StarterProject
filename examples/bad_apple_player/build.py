#!/usr/bin/env python3
"""Build the monochrome movie-player sample as a donor-free G1 MBA."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("build/movie-player"))
    parser.add_argument("--video", type=Path)
    parser.add_argument("--audio", type=Path)
    parser.add_argument("--max-frames", type=int, default=300)
    parser.add_argument("--install-nand", action="store_true")
    args = parser.parse_args()

    here = Path(__file__).resolve().parent
    root = here.parents[1]
    output = args.output_dir.resolve()
    generated = output / "generated_media"
    generate = [
        sys.executable,
        str(here / "generate_media.py"),
        str(generated),
        "--max-frames",
        str(args.max_frames),
    ]
    if args.video is not None:
        generate.extend(("--video", str(args.video)))
    if args.audio is not None:
        generate.extend(("--audio", str(args.audio)))
    subprocess.run(generate, check=True)

    command = [
        sys.executable,
        str(root / "tools/build/build_sdk_app.py"),
        str(here / "main.c"),
        "--output-dir",
        str(output),
        "--slot",
        "G1",
        "--name",
        "MonochromeMoviePlayer",
        "--without-system-ui",
        "--extra-source",
        str(generated / "generated_media.c"),
    ]
    if args.install_nand:
        command.append("--install-nand")
    subprocess.run(command, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
