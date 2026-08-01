#!/usr/bin/env python3

import importlib.util
from pathlib import Path
import unittest


TOOL = (
    Path(__file__).resolve().parents[1]
    / "tools"
    / "assets"
    / "pack_bitmap_2bpp.py"
)
SPEC = importlib.util.spec_from_file_location("pack_bitmap_2bpp", TOOL)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class PackBitmap2bppTest(unittest.TestCase):
    def test_known_order_and_round_trip(self):
        pixels = [0, 1, 2, 3, 3, 2, 1, 0]
        packed = MODULE.pack_indices(4, 2, pixels)
        self.assertEqual(packed, bytes((0x1B, 0xE4)))
        self.assertEqual(MODULE.unpack_indices(4, 2, packed), pixels)

    def test_width_must_preserve_rows(self):
        with self.assertRaises(ValueError):
            MODULE.pack_indices(6, 1, [0] * 6)


if __name__ == "__main__":
    unittest.main()
