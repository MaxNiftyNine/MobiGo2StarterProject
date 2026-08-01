#!/usr/bin/env python3
"""Convert a video to the MobiGo 2 player's 1-bpp delta/RLE word stream."""

import argparse
import subprocess
import struct
from pathlib import Path

import imageio_ffmpeg


def runs(delta):
    i = 0
    while i < len(delta):
        nonzero = delta[i] != 0
        j = i + 1
        while j < len(delta) and (delta[j] != 0) == nonzero and j - i < 0x7FFF:
            j += 1
        yield nonzero, delta[i:j]
        i = j


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("--fps", type=int, default=10)
    ap.add_argument("--threshold", type=int, default=128)
    ap.add_argument("--max-frames", type=int, default=500)
    ap.add_argument("--width", type=int, default=64)
    ap.add_argument("--height", type=int, default=48)
    args = ap.parse_args()

    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    command = [ffmpeg, "-v", "error", "-i", str(args.input), "-vf",
               f"fps={args.fps},scale={args.width}:{args.height}:force_original_aspect_ratio=decrease,"
               f"pad={args.width}:{args.height}:(ow-iw)/2:(oh-ih)/2:black,format=gray",
               "-frames:v", str(args.max_frames), "-f", "rawvideo", "-"]
    proc = subprocess.Popen(command, stdout=subprocess.PIPE)
    frame_bytes = args.width * args.height
    if frame_bytes % 16:
        raise RuntimeError("width * height must be divisible by 16")
    previous = [0] * (frame_bytes // 16)
    frame_count = 0
    total_words = 0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("wb") as out:
        while True:
            raw = proc.stdout.read(frame_bytes)
            if not raw:
                break
            if len(raw) != frame_bytes:
                raise RuntimeError("truncated ffmpeg frame")
            current = []
            for base in range(0, frame_bytes, 16):
                word = 0
                for value in raw[base:base + 16]:
                    word = (word << 1) | (value >= args.threshold)
                current.append(word)
            delta = [a ^ b for a, b in zip(current, previous)]
            encoded = []
            for literal, values in runs(delta):
                encoded.append(len(values) | (0x8000 if literal else 0))
                if literal:
                    encoded.extend(values)
            out.write(struct.pack("<H", len(encoded)))
            out.write(struct.pack(f"<{len(encoded)}H", *encoded))
            total_words += len(encoded) + 1
            frame_count += 1
            previous = current
    if proc.wait() != 0:
        raise RuntimeError("ffmpeg failed")
    print(f"frames={frame_count} fps={args.fps} words={total_words} bytes={total_words * 2}")


if __name__ == "__main__":
    main()
