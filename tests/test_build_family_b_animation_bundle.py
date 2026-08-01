import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "assets" / "build_family_b_animation_bundle.py"
SPEC = importlib.util.spec_from_file_location("animation_builder", TOOL)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
sys.path.insert(0, str(ROOT / "tools" / "assets"))
try:
    SPEC.loader.exec_module(MODULE)
finally:
    sys.path.pop(0)


class FamilyBAnimationBundleTests(unittest.TestCase):
    def test_graph_and_generated_c(self):
        bundle, primary, manifest, frames = MODULE.build_resources()
        self.assertEqual(manifest["record_count"], 2)
        self.assertEqual(manifest["record_delta_x"], [0, 4])
        self.assertEqual(len(frames), 2)
        self.assertGreater(len(bundle), 100)
        self.assertEqual(len(primary), 1088)
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            MODULE.write_outputs(output, "test_animation")
            subprocess.run(
                [
                    "cc", "-I", str(ROOT / "include"), "-I", str(output),
                    "-std=c99", "-Wall", "-Wextra", "-Werror", "-c",
                    str(output / "test_animation_resources.c"),
                    "-o", str(output / "test_animation_resources.o"),
                ],
                check=True,
            )


if __name__ == "__main__":
    unittest.main()
