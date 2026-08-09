from __future__ import annotations

import importlib.util
from pathlib import Path
import struct
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "assets" / "build_menu_art.py"
spec = importlib.util.spec_from_file_location("build_menu_art", SCRIPT)
assert spec is not None and spec.loader is not None
menu = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = menu
spec.loader.exec_module(menu)


class MenuArtTests(unittest.TestCase):
    def test_ppm_becomes_baked_mba_header_assets(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "icon.ppm"
            source.write_bytes(
                b"P6\n2 2\n255\n"
                + bytes((255, 0, 255, 255, 0, 0, 0, 255, 0, 0, 0, 255))
            )
            tile, palette = menu.convert(source)
            self.assertEqual(len(tile), 64 * 104 // 2)
            self.assertEqual(len(palette), 32)
            self.assertTrue(struct.unpack_from("<H", palette, 0)[0] & 0x8000)
            self.assertIn(0, tile)

    def test_checked_in_icon_rebuild_is_deterministic(self) -> None:
        tile, palette = menu.convert(ROOT / "assets" / "menu_icon.ppm")
        with tempfile.TemporaryDirectory() as temporary:
            menu.write(Path(temporary), ROOT / "assets" / "menu_icon.ppm")
            self.assertEqual((Path(temporary) / "menu_tile.bin").read_bytes(), tile)
            self.assertEqual((Path(temporary) / "menu_palette.bin").read_bytes(), palette)


if __name__ == "__main__":
    unittest.main()
