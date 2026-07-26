#!/usr/bin/env python3
"""Make a compact GPL16250 unsigned 8-bit PCM loop from a WAV file."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--start", type=float, default=22.0)
    parser.add_argument("--duration", type=float, default=4.6)
    parser.add_argument("--rate", type=int, default=4000)
    parser.add_argument("--ffmpeg", default="ffmpeg")
    args = parser.parse_args()

    if shutil.which(args.ffmpeg) is None and not Path(args.ffmpeg).exists():
        raise SystemExit(f"ffmpeg not found: {args.ffmpeg}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as temporary:
        raw_path = Path(temporary) / "loop.u8"
        fade_out = max(0.0, args.duration - 0.04)
        subprocess.run(
            [
                args.ffmpeg,
                "-hide_banner",
                "-loglevel",
                "error",
                "-ss",
                str(args.start),
                "-t",
                str(args.duration),
                "-i",
                str(args.source),
                "-af",
                f"afade=t=in:st=0:d=0.04,afade=t=out:st={fade_out}:d=0.04",
                "-ac",
                "1",
                "-ar",
                str(args.rate),
                "-c:a",
                "pcm_u8",
                "-f",
                "u8",
                str(raw_path),
            ],
            check=True,
        )
        pcm = bytearray(raw_path.read_bytes())

    # 0xffff at a word boundary is the SPU terminator. Avoid accidental
    # terminators in the waveform, then append one deliberately.
    for index, sample in enumerate(pcm):
        if sample == 0xFF:
            pcm[index] = 0xFE
    if len(pcm) & 1:
        pcm.append(0x80)
    pcm.extend((0xFF, 0xFF))
    args.output.write_bytes(pcm)
    seconds = (len(pcm) - 2) / args.rate
    print(
        f"samples={len(pcm) - 2} rate={args.rate} "
        f"seconds={seconds:.3f} bytes={len(pcm)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
