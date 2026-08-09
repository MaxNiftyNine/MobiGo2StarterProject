#!/usr/bin/env python3
"""Convert a PCM WAV to the simple unsigned PCM8 stream used by MobiGo W audio."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import struct
import wave


def read_wav(path: Path) -> tuple[list[int], int, int, int]:
    with wave.open(str(path), "rb") as source:
        channels = source.getnchannels()
        width = source.getsampwidth()
        rate = source.getframerate()
        frames = source.getnframes()
        raw = source.readframes(frames)
    if channels < 1 or width not in (1, 2):
        raise ValueError("input must be 8-bit or 16-bit PCM WAV")
    samples: list[int] = []
    if width == 1:
        values = [(value - 128) << 8 for value in raw]
    else:
        values = list(struct.unpack(f"<{len(raw) // 2}h", raw))
    for frame in range(frames):
        start = frame * channels
        samples.append(sum(values[start : start + channels]) // channels)
    return samples, rate, channels, width


def resample(samples: list[int], source_rate: int, target_rate: int) -> list[int]:
    count = max(1, (len(samples) * target_rate + source_rate // 2) // source_rate)
    output: list[int] = []
    for index in range(count):
        position = index * source_rate
        left = min(len(samples) - 1, position // target_rate)
        fraction = position % target_rate
        right = min(len(samples) - 1, left + 1)
        value = (
            samples[left] * (target_rate - fraction) + samples[right] * fraction
        ) // target_rate
        output.append(value)
    return output


def write(source: Path, output: Path, prefix: str, sample_rate: int) -> None:
    samples, source_rate, channels, width = read_wav(source)
    converted = resample(samples, source_rate, sample_rate)
    pcm = bytearray(max(0, min(255, (value + 32768) >> 8)) for value in converted)
    if len(pcm) & 1:
        pcm += b"\x80"
    # A word-aligned 0xffff is the SPU end marker, so escape accidental full-
    # scale sample pairs inside the waveform without otherwise clipping it.
    for offset in range(0, len(pcm), 2):
        if pcm[offset] == 0xff and pcm[offset + 1] == 0xff:
            pcm[offset + 1] = 0xfe
    stream = bytes(pcm) + b"\xff\xff\x00\x00"
    output.mkdir(parents=True, exist_ok=True)
    binary = output / f"{prefix}.pcm8.bin"
    manifest = output / f"{prefix}.pcm8.json"
    binary.write_bytes(stream)
    manifest.write_text(json.dumps({
        "schema": 1,
        "provenance": "Unsigned mono PCM8 conversion for the physically verified W-resource path.",
        "source": {
            "sample_rate": source_rate,
            "channels": channels,
            "sample_width": width,
            "sample_count": len(samples),
        },
        "output": {
            "sample_rate": sample_rate,
            "sample_count": len(converted),
            "byte_count": len(stream),
            "word_count": len(stream) // 2,
        },
    }, indent=2) + "\n", encoding="ascii")
    preview = output / f"{prefix}.preview.wav"
    with wave.open(str(preview), "wb") as target:
        target.setnchannels(1)
        target.setsampwidth(1)
        target.setframerate(sample_rate)
        target.writeframes(bytes(pcm[:len(converted)]))
    print(
        f"PASS PCM8 samples={len(converted)} words={len(stream)//2} "
        f"rate={sample_rate} output={output}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--prefix", default="audio")
    parser.add_argument("--sample-rate", type=int, default=1800)
    args = parser.parse_args()
    if args.sample_rate < 1000 or args.sample_rate > 24000:
        parser.error("sample rate must be between 1000 and 24000 Hz")
    write(args.source, args.output, args.prefix, args.sample_rate)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
