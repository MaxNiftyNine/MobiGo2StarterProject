#!/usr/bin/env python3
"""Convert PCM WAV audio into clean-room MobiGo SPU ADPCM36 assets.

The recovered hardware stream uses 32-sample frames. Each frame contains one
16-bit header followed by eight 16-bit words holding four low-nibble-first
samples each. The header stores a four-bit right shift and a signed six-bit
first-order predictor coefficient. A stream ends with a dummy header followed
by a 0xffff data word.

This offline encoder searches every recovered predictor/shift combination for
each frame and exactly simulates the SPU decoder while choosing nibbles. It
emits a const C array, a header, raw little-endian words, a decoded preview WAV,
and a JSON manifest. No retail audio data or encoder implementation is used.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import struct
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


SAMPLES_PER_FRAME = 32
DATA_WORDS_PER_FRAME = 8
WORDS_PER_FRAME = 9
END_WORDS = (0x0000, 0xFFFF)


@dataclass(frozen=True)
class WavInfo:
    sample_rate: int
    channels: int
    sample_width: int
    frame_count: int


@dataclass(frozen=True)
class EncodedAudio:
    words: tuple[int, ...]
    decoded_samples: tuple[int, ...]
    frame_count: int
    original_sample_count: int
    padded_sample_count: int
    sample_rate: int
    squared_error: int
    peak_error: int


def c_identifier(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_]", "_", value)
    if not cleaned:
        cleaned = "mobigo_audio"
    if cleaned[0].isdigit():
        cleaned = "audio_" + cleaned
    return cleaned[:64]


def clamp_s16(value: int) -> int:
    return max(-32768, min(32767, value))


def signed_nibble(nibble: int) -> int:
    return nibble if nibble < 8 else nibble - 16


def decode_frame(
    words: Sequence[int], previous_sample: int = 0
) -> tuple[list[int], int]:
    if len(words) != WORDS_PER_FRAME:
        raise ValueError("ADPCM36 frame must contain exactly nine words")
    header = words[0]
    shift = header & 0x0F
    filter_coefficient = (header >> 4) & 0x3F
    if filter_coefficient & 0x20:
        filter_coefficient -= 0x40
    step = 1 << (12 - shift)
    decoded: list[int] = []
    previous = previous_sample
    for packed in words[1:]:
        for nibble_index in range(4):
            nibble = (packed >> (nibble_index * 4)) & 0x0F
            prediction = (previous * filter_coefficient + 32) >> 12
            sample = clamp_s16(prediction + signed_nibble(nibble) * step)
            decoded.append(sample)
            previous = sample
    return decoded, previous


def _best_nibble(target: int, prediction: int, step: int) -> tuple[int, int, int]:
    ideal = (target - prediction) / step
    rounded = int(math.floor(ideal + 0.5)) if ideal >= 0 else int(math.ceil(ideal - 0.5))
    candidates = {max(-8, min(7, rounded + delta)) for delta in (-1, 0, 1)}
    best: tuple[int, int, int] | None = None
    for quantized in candidates:
        decoded = clamp_s16(prediction + quantized * step)
        error = target - decoded
        candidate = (error * error, abs(quantized), quantized)
        if best is None or candidate < best:
            best = candidate
            best_decoded = decoded
    assert best is not None
    return best[2] & 0x0F, best_decoded, best[0]


def encode_frame_adaptive(
    samples: Sequence[int], previous_sample: int = 0
) -> tuple[list[int], list[int], int, int]:
    if len(samples) != SAMPLES_PER_FRAME:
        raise ValueError("ADPCM36 encoder requires exactly 32 samples")

    best_key: tuple[int, int, int, int] | None = None
    best_words: list[int] | None = None
    best_decoded: list[int] | None = None
    best_previous = previous_sample

    for filter_coefficient in range(-32, 32):
        for shift in range(13):
            step = 1 << (12 - shift)
            previous = previous_sample
            nibbles: list[int] = []
            decoded: list[int] = []
            squared_error = 0
            for target in samples:
                prediction = (previous * filter_coefficient + 32) >> 12
                nibble, current, error = _best_nibble(target, prediction, step)
                nibbles.append(nibble)
                decoded.append(current)
                previous = current
                squared_error += error

            # Prefer lower error, then a simpler predictor, then finer shift.
            key = (squared_error, abs(filter_coefficient), -shift, filter_coefficient)
            if best_key is None or key < best_key:
                header = ((filter_coefficient & 0x3F) << 4) | shift
                words = [header]
                for word_index in range(DATA_WORDS_PER_FRAME):
                    packed = 0
                    for nibble_index in range(4):
                        packed |= nibbles[word_index * 4 + nibble_index] << (
                            nibble_index * 4
                        )
                    words.append(packed)
                best_key = key
                best_words = words
                best_decoded = decoded
                best_previous = previous

    assert best_key is not None and best_words is not None and best_decoded is not None
    return best_words, best_decoded, best_previous, best_key[0]


def encode_frame_predictor_zero(
    samples: Sequence[int]
) -> tuple[list[int], list[int], int, int]:
    if len(samples) != SAMPLES_PER_FRAME:
        raise ValueError("ADPCM36 encoder requires exactly 32 samples")
    shift = 0
    for candidate in range(12, -1, -1):
        step = 1 << (12 - candidate)
        if all(-8 * step <= sample <= 7 * step for sample in samples):
            shift = candidate
            break
    step = 1 << (12 - shift)
    nibbles: list[int] = []
    decoded: list[int] = []
    squared_error = 0
    for target in samples:
        nibble, current, error = _best_nibble(target, 0, step)
        nibbles.append(nibble)
        decoded.append(current)
        squared_error += error
    words = [shift]
    for word_index in range(DATA_WORDS_PER_FRAME):
        packed = 0
        for nibble_index in range(4):
            packed |= nibbles[word_index * 4 + nibble_index] << (nibble_index * 4)
        words.append(packed)
    return words, decoded, decoded[-1], squared_error


def encode_samples(
    samples: Sequence[int], sample_rate: int, *, adaptive: bool = True
) -> EncodedAudio:
    if sample_rate <= 0:
        raise ValueError("sample rate must be positive")
    original_count = len(samples)
    if original_count == 0:
        raise ValueError("input WAV contains no samples")
    padded = [clamp_s16(int(sample)) for sample in samples]
    while len(padded) % SAMPLES_PER_FRAME:
        padded.append(0)

    words: list[int] = []
    decoded: list[int] = []
    previous = 0
    squared_error = 0
    encoder = encode_frame_adaptive if adaptive else encode_frame_predictor_zero
    for offset in range(0, len(padded), SAMPLES_PER_FRAME):
        frame = padded[offset : offset + SAMPLES_PER_FRAME]
        if adaptive:
            frame_words, frame_decoded, previous, frame_error = encoder(frame, previous)
        else:
            frame_words, frame_decoded, previous, frame_error = encoder(frame)
        words.extend(frame_words)
        decoded.extend(frame_decoded)
        squared_error += frame_error
    words.extend(END_WORDS)
    peak_error = max(abs(a - b) for a, b in zip(padded, decoded))
    return EncodedAudio(
        words=tuple(words),
        decoded_samples=tuple(decoded),
        frame_count=len(padded) // SAMPLES_PER_FRAME,
        original_sample_count=original_count,
        padded_sample_count=len(padded),
        sample_rate=sample_rate,
        squared_error=squared_error,
        peak_error=peak_error,
    )


def _decode_pcm_sample(raw: bytes, sample_width: int) -> int:
    if sample_width == 1:
        return (raw[0] - 128) << 8
    if sample_width == 2:
        return struct.unpack("<h", raw)[0]
    if sample_width == 3:
        value = raw[0] | (raw[1] << 8) | (raw[2] << 16)
        if value & 0x800000:
            value -= 1 << 24
        return clamp_s16(value >> 8)
    if sample_width == 4:
        return clamp_s16(struct.unpack("<i", raw)[0] >> 16)
    raise ValueError(f"unsupported PCM sample width: {sample_width} bytes")


def read_wav(path: Path) -> tuple[list[int], WavInfo]:
    with wave.open(str(path), "rb") as source:
        if source.getcomptype() != "NONE":
            raise ValueError("only uncompressed PCM WAV files are supported")
        channels = source.getnchannels()
        sample_width = source.getsampwidth()
        sample_rate = source.getframerate()
        frame_count = source.getnframes()
        if channels <= 0:
            raise ValueError("WAV channel count must be positive")
        raw = source.readframes(frame_count)
    frame_bytes = channels * sample_width
    if len(raw) != frame_count * frame_bytes:
        raise ValueError("truncated WAV sample data")
    samples: list[int] = []
    for frame_offset in range(0, len(raw), frame_bytes):
        total = 0
        for channel in range(channels):
            start = frame_offset + channel * sample_width
            total += _decode_pcm_sample(raw[start : start + sample_width], sample_width)
        samples.append(clamp_s16(int(round(total / channels))))
    return samples, WavInfo(sample_rate, channels, sample_width, frame_count)


def resample_linear(samples: Sequence[int], source_rate: int, target_rate: int) -> list[int]:
    if source_rate <= 0 or target_rate <= 0:
        raise ValueError("sample rates must be positive")
    if source_rate == target_rate:
        return list(samples)
    output_count = max(1, int(round(len(samples) * target_rate / source_rate)))
    result: list[int] = []
    for output_index in range(output_count):
        source_position = output_index * source_rate / target_rate
        lower = min(int(source_position), len(samples) - 1)
        upper = min(lower + 1, len(samples) - 1)
        fraction = source_position - lower
        value = samples[lower] * (1.0 - fraction) + samples[upper] * fraction
        result.append(clamp_s16(int(round(value))))
    return result


def words_to_bytes(words: Iterable[int]) -> bytes:
    return b"".join(struct.pack("<H", word & 0xFFFF) for word in words)


def c_words(words: Sequence[int], indent: str = "    ") -> str:
    lines = []
    for offset in range(0, len(words), 8):
        chunk = ", ".join(f"0x{word:04x}" for word in words[offset : offset + 8])
        lines.append(indent + chunk + ",")
    return "\n".join(lines)


def write_preview(path: Path, samples: Sequence[int], sample_rate: int) -> None:
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(sample_rate)
        output.writeframes(b"".join(struct.pack("<h", clamp_s16(v)) for v in samples))


def quality_metrics(source: Sequence[int], encoded: EncodedAudio) -> dict[str, object]:
    decoded = encoded.decoded_samples[: len(source)]
    error_power = sum((a - b) ** 2 for a, b in zip(source, decoded))
    signal_power = sum(a * a for a in source)
    mse = error_power / len(source)
    rmse = math.sqrt(mse)
    if error_power == 0:
        snr_db: float | str = "infinite"
    elif signal_power == 0:
        snr_db = float("-inf")
    else:
        snr_db = 10.0 * math.log10(signal_power / error_power)
    return {
        "mse": mse,
        "rmse": rmse,
        "peak_absolute_error": encoded.peak_error,
        "snr_db": snr_db,
    }


def write_outputs(
    output_dir: Path,
    prefix: str,
    encoded: EncodedAudio,
    source_samples: Sequence[int],
    wav_info: WavInfo,
    *,
    adaptive: bool,
    hold_envelope_ticks: int | None = None,
) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    ident = c_identifier(prefix)
    upper = ident.upper()
    payload_words = list(encoded.words)
    envelope_word_offset: int | None = None
    if hold_envelope_ticks is not None:
        if not 0 <= hold_envelope_ticks <= 0xFF:
            raise ValueError("hold envelope ticks must be in range 0..255")
        envelope_word_offset = len(payload_words)
        payload_words.extend((0x7F7F, hold_envelope_ticks))
    raw = words_to_bytes(payload_words)
    stream_bytes = len(encoded.words) * 2
    header_name = f"{ident}_adpcm36.h"
    source_name = f"{ident}_adpcm36.c"
    binary_name = f"{ident}.adpcm36.bin"
    preview_name = f"{ident}.decoded.wav"
    manifest_name = f"{ident}.adpcm36.json"

    header = f"""#ifndef {upper}_ADPCM36_H
#define {upper}_ADPCM36_H

#include \"mobigo_sdk/system_controls.h\"

#define {upper}_ADPCM36_SAMPLE_RATE ((mg_sdk_u32){encoded.sample_rate}UL)
#define {upper}_ADPCM36_SAMPLE_COUNT ((mg_sdk_u32){encoded.original_sample_count}UL)
#define {upper}_ADPCM36_PADDED_SAMPLE_COUNT ((mg_sdk_u32){encoded.padded_sample_count}UL)
#define {upper}_ADPCM36_FRAME_COUNT {encoded.frame_count}
#define {upper}_ADPCM36_STREAM_WORD_COUNT {len(encoded.words)}
#define {upper}_ADPCM36_STREAM_BYTE_COUNT ((mg_sdk_u32){stream_bytes}UL)
#define {upper}_ADPCM36_WORD_COUNT {len(payload_words)}
#define {upper}_ADPCM36_BYTE_COUNT ((mg_sdk_u32){len(raw)}UL)
"""
    if envelope_word_offset is not None:
        header += (
            f"#define {upper}_ADPCM36_ENVELOPE_WORD_OFFSET "
            f"{envelope_word_offset}\n"
        )
    header += f"""

extern const mg_sdk_u16 {ident}_adpcm36_words[{len(payload_words)}];

#endif
"""
    source = f"""#include \"{header_name}\"

/* Clean-room ADPCM36 data generated from {wav_info.frame_count} PCM WAV frames. */
const mg_sdk_u16 {ident}_adpcm36_words[{len(payload_words)}] = {{
{c_words(payload_words)}
}};
"""
    (output_dir / header_name).write_text(header, encoding="ascii")
    (output_dir / source_name).write_text(source, encoding="ascii")
    (output_dir / binary_name).write_bytes(raw)
    write_preview(
        output_dir / preview_name,
        encoded.decoded_samples[: encoded.original_sample_count],
        encoded.sample_rate,
    )

    metrics = quality_metrics(source_samples, encoded)
    manifest: dict[str, object] = {
        "schema": 1,
        "provenance": (
            "Clean-room PCM WAV conversion using the recovered SPU ADPCM36 "
            "frame/decoder grammar; no retail sample bytes are consumed."
        ),
        "encoder": "adaptive-first-order" if adaptive else "predictor-zero",
        "source": {
            "sample_rate": wav_info.sample_rate,
            "channels": wav_info.channels,
            "sample_width_bytes": wav_info.sample_width,
            "frame_count": wav_info.frame_count,
        },
        "output": {
            "sample_rate": encoded.sample_rate,
            "sample_count": encoded.original_sample_count,
            "padded_sample_count": encoded.padded_sample_count,
            "frame_count": encoded.frame_count,
            "stream_word_count": len(encoded.words),
            "stream_byte_count": stream_bytes,
            "word_count": len(payload_words),
            "byte_count": len(raw),
            "envelope_word_offset": envelope_word_offset,
            "compression_ratio_vs_pcm16": stream_bytes
            / (encoded.original_sample_count * 2),
            "sha256": hashlib.sha256(raw).hexdigest(),
        },
        "quality": metrics,
        "files": {
            "header": header_name,
            "source": source_name,
            "binary": binary_name,
            "decoded_preview": preview_name,
        },
    }
    (output_dir / manifest_name).write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_wav", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--prefix", help="C identifier/output prefix")
    parser.add_argument(
        "--sample-rate",
        type=int,
        help="linearly resample before encoding; default preserves source rate",
    )
    parser.add_argument(
        "--predictor-zero",
        action="store_true",
        help="use the simple independent-frame encoder instead of adaptive search",
    )
    parser.add_argument(
        "--hold-envelope",
        type=int,
        metavar="TICKS",
        help=(
            "append the two-word 0x7f7f hold envelope used by clean M patch "
            "zones; TICKS must be 0..255"
        ),
    )
    args = parser.parse_args()

    input_wav = args.input_wav.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()
    if not input_wav.is_file():
        raise SystemExit(f"input WAV does not exist: {input_wav}")
    samples, wav_info = read_wav(input_wav)
    sample_rate = args.sample_rate or wav_info.sample_rate
    samples = resample_linear(samples, wav_info.sample_rate, sample_rate)
    encoded = encode_samples(samples, sample_rate, adaptive=not args.predictor_zero)
    prefix = args.prefix or input_wav.stem
    manifest = write_outputs(
        output_dir,
        prefix,
        encoded,
        samples,
        wav_info,
        adaptive=not args.predictor_zero,
        hold_envelope_ticks=args.hold_envelope,
    )
    output = manifest["output"]
    quality = manifest["quality"]
    print(
        "PASS ADPCM36 "
        f"samples={output['sample_count']} frames={output['frame_count']} "
        f"words={output['word_count']} rate={output['sample_rate']} "
        f"rmse={quality['rmse']:.2f} output={output_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
