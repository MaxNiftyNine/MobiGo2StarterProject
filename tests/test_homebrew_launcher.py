from __future__ import annotations

import importlib.util
from pathlib import Path
import struct
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "homebrew_launcher"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


catalog = load_module("homebrew_catalog", EXAMPLE / "catalog.py")
waves = load_module("homebrew_waves", EXAMPLE / "generate_wave_bundle.py")
icons = load_module("homebrew_icons", EXAMPLE / "generate_icon_bundle.py")
fonts = load_module(
    "homebrew_fonts", ROOT / "tools" / "assets" / "build_clean_font_bundle.py"
)


class CatalogTests(unittest.TestCase):
    def test_round_trip_preserves_launcher_metadata(self) -> None:
        entries = [
            catalog.CatalogEntry(
                r"A:\HB\Pong.MBA", "Pong", "Classic paddle game", "Max", 1, 0x1234
            ),
            catalog.CatalogEntry(
                r"A:\HB\System.MBA", "System Menu", "Original menu", "VTech", 5
            ),
        ]
        encoded = catalog.encode_catalog(entries)
        self.assertEqual(encoded[:4], b"HB02")
        self.assertEqual(catalog.decode_catalog(encoded), entries)

    def test_legacy_catalog_still_decodes(self) -> None:
        path = r"A:\HB\Pong.MBA".encode("ascii").ljust(42, b"\0")
        label = b"Pong.MBA".ljust(20, b"\0")
        encoded = b"HB01" + struct.pack("<HH", 1, 64) + path + label + struct.pack("<H", 7)
        self.assertEqual(
            catalog.decode_catalog(encoded),
            [catalog.CatalogEntry(r"A:\HB\Pong.MBA", "Pong.MBA", flags=7)],
        )

    def test_full_catalog_fits_target_buffer(self) -> None:
        entries = [
            catalog.CatalogEntry(fr"A:\HB\APP{i:02}.MBA", f"APP{i:02}.MBA")
            for i in range(catalog.MAX_ENTRIES)
        ]
        encoded = catalog.encode_catalog(entries)
        self.assertEqual(len(encoded), 1544)
        self.assertEqual(len(catalog.decode_catalog(encoded)), 16)

    def test_rejects_non_ascii_and_overlong_fields(self) -> None:
        with self.assertRaises(ValueError):
            catalog.encode_catalog([catalog.CatalogEntry(r"A:\\HB\\CAFE.MBA", "Café.MBA")])
        with self.assertRaises(ValueError):
            catalog.encode_catalog([catalog.CatalogEntry("A" * 42, "Long.MBA")])

    def test_rejects_truncated_or_wrong_magic(self) -> None:
        with self.assertRaises(ValueError):
            catalog.decode_catalog(b"retail sort data")
        good = catalog.encode_catalog(
            [catalog.CatalogEntry(r"A:\HB\Pong.MBA", "Pong.MBA")]
        )
        with self.assertRaises(ValueError):
            catalog.decode_catalog(good[:-1])


class WaveBundleTests(unittest.TestCase):
    def test_generated_bundle_is_a_fast_full_screen_wave(self) -> None:
        bundle, primary, manifest = waves.build_resources()
        self.assertIn("sine-wave artwork", manifest["provenance"])
        self.assertEqual(manifest["wave_frames"], 4)
        self.assertEqual(manifest["wave_duration"], 2)
        self.assertGreater(manifest["background_unique_tiles"], 20)
        self.assertEqual(len(bundle), manifest["bundle_word_count"])
        self.assertEqual(len(primary), manifest["primary_word_count"])
        self.assertLessEqual(len(bundle), 256)
        self.assertGreater(len(set(primary)), 20)

    def test_write_outputs_is_reproducible(self) -> None:
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            waves.write_outputs(Path(first), "hb_wave")
            waves.write_outputs(Path(second), "hb_wave")
            for name in ("bundle.bin", "primary.bin", "manifest.json", "hb_wave_resources.c"):
                self.assertEqual((Path(first) / name).read_bytes(), (Path(second) / name).read_bytes())


class MbaIconBundleTests(unittest.TestCase):
    def test_three_runtime_icons_use_full_mba_artwork_area(self) -> None:
        bundle = icons.build_bundle()
        self.assertLessEqual(len(bundle), 176)
        self.assertEqual(icons.PRIMARY_WORDS, 1792)
        self.assertEqual(icons.ICON_WORDS, 256)
        self.assertEqual(bundle[0x0A], 3)
        self.assertEqual(bundle[0x16], 1)
        self.assertIn(0, bundle)

    def test_icon_generator_is_reproducible(self) -> None:
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            icons.write_outputs(Path(first), "hb_icon")
            icons.write_outputs(Path(second), "hb_icon")
            for name in ("bundle.bin", "hb_icon_resources.c", "hb_icon_resources.h"):
                self.assertEqual((Path(first) / name).read_bytes(), (Path(second) / name).read_bytes())


class CompactFontTests(unittest.TestCase):
    def test_launcher_font_keeps_ascii_ui_but_uses_smaller_graph(self) -> None:
        compact = fonts.build_resources(96)
        full = fonts.build_resources(128)
        self.assertEqual(compact[2]["record_count"], 96)
        self.assertTrue(compact[2]["lowercase_maps_to_uppercase"])
        self.assertLess(len(compact[0]), len(full[0]))
        self.assertEqual(len(compact[1]), len(full[1]))


if __name__ == "__main__":
    unittest.main()
