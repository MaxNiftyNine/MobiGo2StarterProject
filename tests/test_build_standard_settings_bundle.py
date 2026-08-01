import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "assets" / "build_standard_settings_bundle.py"
SPEC = importlib.util.spec_from_file_location("settings_builder", TOOL)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class StandardSettingsBundleTests(unittest.TestCase):
    def test_builds_original_relocatable_graph_and_c_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            manifest = MODULE.write_outputs(output, "test_settings")

            bundle = output.joinpath("bundle.bin").read_bytes()
            primary = output.joinpath("primary.bin").read_bytes()
            self.assertEqual(bundle[:4], bytes((2, 0, 0, 128)))
            self.assertEqual(len(bundle), manifest["bundle_word_count"] * 2)
            self.assertEqual(len(primary), manifest["primary_word_count"] * 2)
            self.assertEqual(manifest["brightness_record_count"], 4)
            self.assertEqual(manifest["volume_record_count"], 10)
            self.assertEqual(len(manifest["images"]), 14)
            self.assertEqual(
                json.loads(output.joinpath("manifest.json").read_text())["schema"],
                1,
            )
            subprocess.run(
                [
                    "cc",
                    "-I",
                    str(ROOT / "include"),
                    "-std=c99",
                    "-Wall",
                    "-Wextra",
                    "-Werror",
                    "-c",
                    str(output / "test_settings_resources.c"),
                    "-o",
                    str(output / "test_settings_resources.o"),
                ],
                check=True,
            )

    def test_generated_pixels_do_not_match_retail_settings_payloads(self):
        _, primary, manifest, _ = MODULE.build_resources()
        official = json.loads(
            (ROOT / "research" / "reports" / "asset-bundle-catalog.json").read_text()
        )
        official_hashes = set(official["shared_standard_settings_payloads"])
        for image in manifest["images"]:
            begin = int(image["primary_word_offset"], 0) * 2
            payload = MODULE.words_to_bytes(primary)[
                begin : begin + MODULE.BITMAP_WORDS * 2
            ]
            self.assertNotIn(hashlib.sha256(payload).hexdigest(), official_hashes)


if __name__ == "__main__":
    unittest.main()
