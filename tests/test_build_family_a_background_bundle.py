import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "assets" / "build_family_a_background_bundle.py"
SPEC = importlib.util.spec_from_file_location("family_a_builder", TOOL)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
# Let the generator import its sibling clean-room settings helper.
sys.path.insert(0, str(ROOT / "tools" / "assets"))
try:
    SPEC.loader.exec_module(MODULE)
finally:
    sys.path.pop(0)


class FamilyABackgroundBundleTests(unittest.TestCase):
    def test_builds_original_family_a_graph_and_c_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            manifest = MODULE.write_outputs(output, "test_family_a")
            bundle = output.joinpath("bundle.bin").read_bytes()
            primary = output.joinpath("primary.bin").read_bytes()

            self.assertEqual(bundle[:4], bytes((2, 0, 0, 128)))
            self.assertEqual(len(bundle), manifest["bundle_word_count"] * 2)
            self.assertEqual(len(primary), manifest["primary_word_count"] * 2)
            self.assertEqual(manifest["family_a_descriptor"], 0)
            self.assertEqual(manifest["image"]["width"], 320)
            self.assertEqual(manifest["image"]["height"], 240)
            self.assertEqual(manifest["image"]["cell_width"], 16)
            self.assertEqual(manifest["image"]["cell_height"], 16)
            self.assertEqual(manifest["image"]["format"], 0)

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
                    str(output / "test_family_a_resources.c"),
                    "-o",
                    str(output / "test_family_a_resources.o"),
                ],
                check=True,
            )

    def test_primary_graphics_are_generated_without_retail_inputs(self):
        bundle, primary, manifest = MODULE.build_resources()
        self.assertTrue(bundle)
        image = manifest["image"]
        graphics = int(image["graphics_primary_word_offset"], 0)
        words_per_tile = image["graphics_words_per_tile"]
        self.assertEqual(primary[graphics : graphics + words_per_tile], [0] * words_per_tile)
        self.assertNotEqual(
            primary[graphics + words_per_tile : graphics + 2 * words_per_tile],
            [0] * words_per_tile,
        )


if __name__ == "__main__":
    unittest.main()
