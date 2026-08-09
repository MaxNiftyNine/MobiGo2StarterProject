from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
import wave


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "assets" / "build_pcm8_audio.py"
spec = importlib.util.spec_from_file_location("build_pcm8_audio", SCRIPT)
assert spec is not None and spec.loader is not None
pcm8 = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = pcm8
spec.loader.exec_module(pcm8)


class Pcm8AudioTests(unittest.TestCase):
    def test_conversion_is_mono_unsigned_and_terminated(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source.wav"
            samples = [32767, 32767, 0, -16000] * 100
            with wave.open(str(source), "wb") as output:
                output.setnchannels(1)
                output.setsampwidth(2)
                output.setframerate(4000)
                output.writeframes(struct.pack(f"<{len(samples)}h", *samples))
            pcm8.write(source, root, "test", 2000)
            stream = (root / "test.pcm8.bin").read_bytes()
            manifest = json.loads((root / "test.pcm8.json").read_text())
            self.assertEqual(stream[-4:], b"\xff\xff\0\0")
            self.assertNotIn(b"\xff\xff", stream[:-4])
            self.assertEqual(manifest["output"]["sample_rate"], 2000)
            self.assertEqual(manifest["output"]["byte_count"], len(stream))
            self.assertEqual(len(stream) & 1, 0)


if __name__ == "__main__":
    unittest.main()
