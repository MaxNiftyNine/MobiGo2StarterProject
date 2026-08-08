import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "nand" / "install_mba.py"
SPEC = importlib.util.spec_from_file_location("install_mba_tool", TOOL)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class InstallMbaDefaultsTests(unittest.TestCase):
    def test_defaults_to_maintained_system_slot_and_editor(self):
        args = MODULE.build_parser().parse_args(
            ["source.bin", "application.MBA", "output.bin"]
        )
        self.assertEqual(args.slot, "SY")
        self.assertEqual(args.editor, ROOT / "tools" / "nand" / "nandfs.py")
        self.assertTrue(args.editor.is_file())

    def test_legacy_g1_requires_explicit_selection(self):
        args = MODULE.build_parser().parse_args(
            [
                "--slot",
                "G1",
                "source.bin",
                "application.MBA",
                "output.bin",
            ]
        )
        self.assertEqual(args.slot, "G1")


if __name__ == "__main__":
    unittest.main()
