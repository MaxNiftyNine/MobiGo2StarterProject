import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "re" / "inspect_asset_bundle.py"
SPEC = importlib.util.spec_from_file_location("asset_inspector", TOOL)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class FamilyAInspectorTests(unittest.TestCase):
    def test_parses_renderer_confirmed_family_a_image_fields(self):
        runtime_base = 0x1000
        header = 0x1020
        table_relative = 0x20
        image_relative = 0x40
        slot_relative = 0x80
        table = header + 0x20 + table_relative
        image_record = header + 0x20 + image_relative
        slot = header + 0x20 + slot_relative
        words = [0] * 0x100

        def put(address, values):
            offset = address - runtime_base
            words[offset : offset + len(values)] = values

        # Version-2-ish header fields needed by the inspector.
        put(header + 0x12, [1])
        put(header + 0x14, [table_relative & 0xFFFF, table_relative >> 16])
        put(header + 0x16, [0])
        put(header + 0x18, [0, 0])
        put(
            table,
            [1, 0, 0, 0, 0, 0x40, 0xFFFF, 0xFFFF,
             image_relative & 0xFFFF, image_relative >> 16],
        )
        put(
            image_record,
            [
                320, 240, 16, 16, 2,
                0, 239, 0, 319, 0,
                0x3456, 0x8001,
                0x2345, 0x8001,
                7, 0,
                slot_relative & 0xFFFF, slot_relative >> 16,
            ],
        )
        put(slot, [0, 0])

        encoded = bytearray()
        for word in words:
            encoded += int(word).to_bytes(2, "little")

        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "sample.bin"
            path.write_bytes(encoded)
            image = MODULE.WordImage(path, runtime_base)
            parsed = MODULE.family_a_image_record(image, header, image_relative)

        self.assertEqual(parsed["width"], 320)
        self.assertEqual(parsed["height"], 240)
        self.assertEqual(parsed["cell_width"], 16)
        self.assertEqual(parsed["cell_height"], 16)
        self.assertEqual(parsed["format"], 2)
        self.assertEqual(parsed["graphics_base_pointer"], "0x80013456")
        self.assertEqual(parsed["tilemap_source_pointer"], "0x80012345")
        self.assertEqual(parsed["palette_selector"], 7)
        self.assertEqual(parsed["runtime_slot_word_address"], "0x000010c0")
        self.assertEqual(parsed["runtime_slot_words"], ["0x0000", "0x0000"])


if __name__ == "__main__":
    unittest.main()
