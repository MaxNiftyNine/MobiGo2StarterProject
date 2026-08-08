import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "assets" / "build_system_ui_bundle.py"
SPEC = importlib.util.spec_from_file_location("system_ui_builder", TOOL)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
sys.path.insert(0, str(ROOT / "tools" / "assets"))
try:
    SPEC.loader.exec_module(MODULE)
finally:
    sys.path.pop(0)


class SystemUiBundleTests(unittest.TestCase):
    def test_combines_settings_and_poweroff_descriptors(self):
        bundle, primary, manifest = MODULE.build_resources()
        self.assertEqual(manifest["ui_family_a_count"], 0)
        self.assertEqual(manifest["ui_family_b_count"], 2)
        self.assertEqual(manifest["settings"]["descriptor"], 0)
        self.assertEqual(manifest["settings"]["brightness_record_count"], 4)
        self.assertEqual(manifest["settings"]["volume_record_count"], 10)
        self.assertEqual(manifest["settings"]["brightness_x"], 138)
        self.assertEqual(manifest["settings"]["volume_x"], 109)
        self.assertEqual(manifest["settings"]["y"], 214)
        self.assertEqual(manifest["poweroff"]["descriptor"], 1)
        self.assertEqual(manifest["poweroff"]["chunk_widths"], [64, 64, 32, 16])
        self.assertEqual(len(bundle), 572)
        self.assertLessEqual(len(bundle), 0x0800)
        self.assertEqual(len(primary), 5312)
        self.assertEqual(manifest["auto_instance"]["marker_words"], 4)
        self.assertEqual(manifest["auto_instance"]["handle_words"], 4)

    def test_emitted_facade_host_compiles(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            MODULE.write_outputs(output, "test_system_ui")
            header = output.joinpath("test_system_ui_resources.h").read_text()
            source = output.joinpath("test_system_ui_resources.c").read_text()
            self.assertIn("create_settings", header)
            self.assertIn("create_poweroff", header)
            self.assertIn("show_brightness", header)
            self.assertIn("show_volume", header)
            self.assertIn("show_poweroff", header)
            self.assertIn("hide_poweroff", header)
            self.assertIn("object, 138, 214, 0", source)
            self.assertIn("object, 109, 214, 0", source)
            self.assertIn("bundle_template", source)
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
                    str(output / "test_system_ui_resources.c"),
                    "-o",
                    str(output / "test_system_ui_resources.o"),
                ],
                check=True,
            )


if __name__ == "__main__":
    unittest.main()
