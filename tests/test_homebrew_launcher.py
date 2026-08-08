from __future__ import annotations

import importlib.util
from pathlib import Path
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


class CatalogTests(unittest.TestCase):
    def test_round_trip_preserves_mba_names_and_flags(self) -> None:
        entries = [
            catalog.CatalogEntry(r"A:\HB\Pong.MBA", "Pong.MBA", 0x1234),
            catalog.CatalogEntry(r"A:\HB\SystemMenu.MBA", "SystemMenu.MBA"),
        ]
        encoded = catalog.encode_catalog(entries)
        self.assertEqual(encoded[:4], b"HB01")
        self.assertEqual(catalog.decode_catalog(encoded), entries)

    def test_full_catalog_fits_target_buffer(self) -> None:
        entries = [
            catalog.CatalogEntry(fr"A:\HB\APP{i:02}.MBA", f"APP{i:02}.MBA")
            for i in range(catalog.MAX_ENTRIES)
        ]
        encoded = catalog.encode_catalog(entries)
        self.assertEqual(len(encoded), 1032)
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
    def test_generated_bundle_is_original_light_blue_wave_art(self) -> None:
        bundle, primary, manifest = waves.build_resources()
        self.assertEqual(manifest["provenance"], "Original clean-room light-blue wave artwork.")
        self.assertEqual(manifest["tile_count"], 301)
        self.assertEqual(len(bundle), manifest["bundle_word_count"])
        self.assertEqual(len(primary), manifest["primary_word_count"])
        self.assertGreater(len(set(primary[1088:])), 20)

    def test_write_outputs_is_reproducible(self) -> None:
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            waves.write_outputs(Path(first), "hb_wave")
            waves.write_outputs(Path(second), "hb_wave")
            for name in ("bundle.bin", "primary.bin", "manifest.json", "hb_wave_resources.c"):
                self.assertEqual((Path(first) / name).read_bytes(), (Path(second) / name).read_bytes())


if __name__ == "__main__":
    unittest.main()
