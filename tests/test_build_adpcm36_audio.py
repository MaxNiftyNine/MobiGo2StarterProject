import importlib.util
import json
import math
import struct
import subprocess
import sys
import tempfile
import unittest
import wave
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "assets" / "build_adpcm36_audio.py"
SPEC = importlib.util.spec_from_file_location("adpcm36_builder", TOOL)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class Adpcm36BuilderTests(unittest.TestCase):
    def test_predictor_zero_frame_matches_recovered_decoder(self):
        samples = [12288 if (index & 4) == 0 else -12288 for index in range(32)]
        words, decoded, _previous, error = MODULE.encode_frame_predictor_zero(samples)
        self.assertEqual(words[0], 1)
        self.assertEqual(decoded, samples)
        self.assertEqual(error, 0)
        round_trip, previous = MODULE.decode_frame(words)
        self.assertEqual(round_trip, samples)
        self.assertEqual(previous, samples[-1])

    def test_adaptive_search_is_no_worse_than_predictor_zero(self):
        samples = [int(18000 * math.sin(index * 0.19)) for index in range(32)]
        adaptive = MODULE.encode_frame_adaptive(samples)
        simple = MODULE.encode_frame_predictor_zero(samples)
        self.assertLessEqual(adaptive[3], simple[3])
        decoded, previous = MODULE.decode_frame(adaptive[0])
        self.assertEqual(decoded, adaptive[1])
        self.assertEqual(previous, adaptive[2])

    def test_cli_emits_compilable_deterministic_asset(self):
        with tempfile.TemporaryDirectory() as temporary:
            temporary_path = Path(temporary)
            wav_path = temporary_path / "tone.wav"
            output_a = temporary_path / "a"
            output_b = temporary_path / "b"
            samples = [
                int(14000 * math.sin(2.0 * math.pi * 440.0 * index / 8000.0))
                for index in range(100)
            ]
            with wave.open(str(wav_path), "wb") as destination:
                destination.setnchannels(1)
                destination.setsampwidth(2)
                destination.setframerate(8000)
                destination.writeframes(
                    b"".join(struct.pack("<h", sample) for sample in samples)
                )

            command = [
                sys.executable,
                str(TOOL),
                str(wav_path),
                str(output_a),
                "--prefix",
                "test_tone",
                "--sample-rate",
                "4000",
            ]
            subprocess.run(command, check=True, capture_output=True, text=True)
            command[3] = str(output_b)
            subprocess.run(command, check=True, capture_output=True, text=True)

            manifest = json.loads(
                (output_a / "test_tone.adpcm36.json").read_text()
            )
            self.assertEqual(manifest["output"]["sample_rate"], 4000)
            self.assertEqual(manifest["output"]["sample_count"], 50)
            self.assertEqual(manifest["output"]["padded_sample_count"], 64)
            self.assertEqual(manifest["output"]["frame_count"], 2)
            self.assertEqual(manifest["output"]["word_count"], 20)
            self.assertEqual(manifest["output"]["stream_word_count"], 20)
            self.assertIsNone(manifest["output"]["envelope_word_offset"])
            raw_a = (output_a / "test_tone.adpcm36.bin").read_bytes()
            raw_b = (output_b / "test_tone.adpcm36.bin").read_bytes()
            self.assertEqual(raw_a, raw_b)
            self.assertEqual(struct.unpack_from("<HH", raw_a, len(raw_a) - 4), (0, 0xFFFF))

            subprocess.run(
                [
                    "cc",
                    "-I",
                    str(ROOT / "include"),
                    "-I",
                    str(output_a),
                    "-std=c99",
                    "-Wall",
                    "-Wextra",
                    "-Werror",
                    "-c",
                    str(output_a / "test_tone_adpcm36.c"),
                    "-o",
                    str(output_a / "test_tone_adpcm36.o"),
                ],
                check=True,
            )

    def test_optional_hold_envelope_is_outside_stream_length(self):
        samples = [0] * 32
        encoded = MODULE.encode_samples(samples, 4000)
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            manifest = MODULE.write_outputs(
                output,
                "with_env",
                encoded,
                samples,
                MODULE.WavInfo(4000, 1, 2, 32),
                adaptive=True,
                hold_envelope_ticks=0x55,
            )
            self.assertEqual(manifest["output"]["stream_word_count"], 11)
            self.assertEqual(manifest["output"]["word_count"], 13)
            self.assertEqual(manifest["output"]["envelope_word_offset"], 11)
            raw = (output / "with_env.adpcm36.bin").read_bytes()
            self.assertEqual(struct.unpack_from("<HH", raw, len(raw) - 4), (0x7F7F, 0x55))


if __name__ == "__main__":
    unittest.main()
