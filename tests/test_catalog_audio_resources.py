import importlib.util
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "re" / "catalog_audio_resources.py"
SPEC = importlib.util.spec_from_file_location("audio_catalog", TOOL)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
sys.path.insert(0, str(ROOT / "tools" / "re"))
try:
    SPEC.loader.exec_module(MODULE)
finally:
    sys.path.pop(0)


class AudioCatalogTests(unittest.TestCase):
    def test_g1_and_sy_roots(self):
        mba_dir = ROOT.parent / "MBAs"
        sample_paths = [mba_dir / sample.file for sample in MODULE.SAMPLES]
        if all(path.is_file() for path in sample_paths):
            rows = [
                MODULE.catalog_sample(mba_dir, sample)
                for sample in MODULE.SAMPLES
            ]
        elif any(path.exists() for path in sample_paths):
            self.fail(
                "retail audio-catalog samples are incomplete: "
                + ", ".join(str(path) for path in sample_paths)
            )
        else:
            report = json.loads(
                (ROOT / "research" / "reports" / "audio-resource-catalog.json").read_text()
            )
            self.assertEqual(report["schema"], 1)
            rows = report["samples"]

        self.assertEqual(
            [row["file"] for row in rows],
            [sample.file for sample in MODULE.SAMPLES],
        )
        self.assertEqual(rows[0]["counts"], {"M": 6, "W": 102, "S": 119})
        self.assertEqual(rows[1]["counts"], {"M": 2, "W": 80, "S": 85})
        self.assertEqual(rows[0]["w_invariants"]["sample_rates"], [11025])
        self.assertEqual(rows[1]["w_invariants"]["sample_rates"], [11025])
        self.assertEqual(rows[0]["w_invariants"]["format_flags"], ["0x3cd5"])
        self.assertEqual(rows[1]["w_invariants"]["format_flags"], ["0x3cd5"])
        self.assertEqual(rows[0]["patch_directory"]["melodic_count"], 71)
        self.assertEqual(rows[0]["patch_directory"]["percussion_count"], 34)
        self.assertEqual(rows[1]["patch_directory"]["melodic_count"], 71)
        self.assertEqual(rows[1]["patch_directory"]["percussion_count"], 34)


if __name__ == "__main__":
    unittest.main()
