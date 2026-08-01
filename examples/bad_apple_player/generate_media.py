#!/usr/bin/env python3
"""Generate linkable movie/audio resources for the monochrome player."""

from __future__ import annotations

import argparse
import math
import struct
import subprocess
import sys
import tempfile
from pathlib import Path


WIDTH = 64
HEIGHT = 48
WORDS_PER_FRAME = WIDTH * HEIGHT // 16


def encoded_frame(previous: list[int], current: list[int]) -> list[int]:
    delta = [old ^ new for old, new in zip(previous, current)]
    encoded: list[int] = []
    index = 0
    while index < len(delta):
        literal = delta[index] != 0
        end = index + 1
        while end < len(delta) and (delta[end] != 0) == literal:
            end += 1
        encoded.append((end - index) | (0x8000 if literal else 0))
        if literal:
            encoded.extend(delta[index:end])
        index = end
    return [len(encoded), *encoded]


def synthetic_movie(frame_count: int = 24) -> tuple[bytes, int]:
    """Make an original moving-box clip so a clean checkout always builds."""
    previous = [0] * WORDS_PER_FRAME
    output: list[int] = []
    for frame in range(frame_count):
        pixels = [0] * (WIDTH * HEIGHT)
        box_x = 2 + (frame * 2) % 46
        box_y = 12 + ((frame // 6) & 1) * 8
        for y in range(box_y, box_y + 16):
            for x in range(box_x, box_x + 16):
                pixels[y * WIDTH + x] = 1
        current: list[int] = []
        for base in range(0, len(pixels), 16):
            word = 0
            for pixel in pixels[base : base + 16]:
                word = (word << 1) | pixel
            current.append(word)
        output.extend(encoded_frame(previous, current))
        previous = current
    return struct.pack(f"<{len(output)}H", *output), frame_count


def synthetic_audio(rate: int = 4000, seconds: float = 1.0) -> bytes:
    samples = bytearray()
    count = int(rate * seconds)
    for index in range(count):
        envelope = min(index / 120.0, (count - index) / 120.0, 1.0)
        sample = 128 + int(42.0 * envelope * math.sin(index * 2.0 * math.pi * 220.0 / rate))
        samples.append(min(sample, 0xFE))
    if len(samples) & 1:
        samples.append(0x80)
    samples.extend((0xFF, 0xFF))
    return bytes(samples)


def words(data: bytes) -> tuple[int, ...]:
    if len(data) & 1:
        data += b"\0"
    return struct.unpack(f"<{len(data) // 2}H", data)


def array_text(name: str, values: tuple[int, ...]) -> str:
    lines = []
    for offset in range(0, len(values), 10):
        lines.append("    " + ", ".join(f"0x{value:04x}u" for value in values[offset : offset + 10]))
    return f"const unsigned short {name}[] = {{\n" + ",\n".join(lines) + "\n};\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--video", type=Path, help="media you have permission to encode")
    parser.add_argument("--audio", type=Path, help="audio/video source for the PCM loop")
    parser.add_argument("--max-frames", type=int, default=300)
    args = parser.parse_args()

    here = Path(__file__).resolve().parent
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as temporary:
        temporary_path = Path(temporary)
        if args.video is None:
            movie, frame_count = synthetic_movie()
        else:
            movie_path = temporary_path / "movie.dat"
            result = subprocess.run(
                [
                    sys.executable,
                    str(here / "tools/encode_video.py"),
                    str(args.video.resolve()),
                    str(movie_path),
                    "--max-frames",
                    str(args.max_frames),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            fields = dict(item.split("=", 1) for item in result.stdout.split() if "=" in item)
            frame_count = int(fields["frames"])
            movie = movie_path.read_bytes()

        if args.audio is None:
            audio = synthetic_audio()
        else:
            audio_path = temporary_path / "audio.pcm"
            subprocess.run(
                [
                    sys.executable,
                    str(here / "tools/encode_audio.py"),
                    str(args.audio.resolve()),
                    str(audio_path),
                ],
                check=True,
            )
            audio = audio_path.read_bytes()

    header = (
        "#ifndef SAMPLE_GENERATED_MEDIA_H\n"
        "#define SAMPLE_GENERATED_MEDIA_H\n\n"
        f"#define SAMPLE_MOVIE_FRAME_COUNT {frame_count}u\n"
        "extern const unsigned short sample_movie_words[];\n"
        "extern const unsigned short sample_audio_words[];\n\n"
        "#endif\n"
    )
    source = '#include "generated_media.h"\n\n'
    source += array_text("sample_movie_words", words(movie)) + "\n"
    source += array_text("sample_audio_words", words(audio))
    (output / "generated_media.h").write_text(header, encoding="ascii")
    (output / "generated_media.c").write_text(source, encoding="ascii")
    print(f"frames={frame_count} movie_bytes={len(movie)} audio_bytes={len(audio)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
