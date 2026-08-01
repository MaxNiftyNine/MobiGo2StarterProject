import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "assets" / "build_poweroff_bundle.py"
SPEC = importlib.util.spec_from_file_location("poweroff_builder", TOOL)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
sys.path.insert(0, str(ROOT / "tools" / "assets"))
try:
    SPEC.loader.exec_module(MODULE)
finally:
    sys.path.pop(0)


class PoweroffBundleTests(unittest.TestCase):
    def test_builds_recovered_one_mode_one_record_graph(self):
        bundle, primary, manifest, canvas = MODULE.build_resources()
        self.assertEqual(manifest["ui_family_b_descriptor"], 0)
        self.assertEqual(manifest["mode"], 0)
        self.assertEqual(manifest["record"], 0)
        self.assertEqual(manifest["bitmap"]["width"], 176)
        self.assertEqual(manifest["bitmap"]["height"], 32)
        self.assertEqual(manifest["bitmap"]["chunk_widths"], [64, 64, 32, 16])
        self.assertEqual(len(canvas.pixels), 176 * 32)
        self.assertEqual(len(bundle), manifest["bundle_word_count"])
        self.assertEqual(len(primary), manifest["primary_word_count"])

    def test_emitted_c_is_boot_safe_and_host_compiles(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            MODULE.write_outputs(output, "test_poweroff")
            header = output.joinpath("test_poweroff_resources.h").read_text()
            source = output.joinpath("test_poweroff_resources.c").read_text()
            self.assertIn("bundle_template", header)
            self.assertIn("copy_bundle", header)
            self.assertNotIn("extern unsigned short test_poweroff_bundle_words", header)
            self.assertIn("const unsigned short test_poweroff_bundle_template", source)
            subprocess.run(
                [
                    "cc", "-I", str(ROOT / "include"),
                    "-std=c99", "-Wall", "-Wextra", "-Werror",
                    "-c", str(output / "test_poweroff_resources.c"),
                    "-o", str(output / "test_poweroff_resources.o"),
                ],
                check=True,
            )


if __name__ == "__main__":
    unittest.main()
