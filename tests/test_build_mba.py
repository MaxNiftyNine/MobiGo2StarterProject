from __future__ import annotations

import importlib.util
import struct
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "build" / "build_mba.py"
SPEC = importlib.util.spec_from_file_location("mba_builder", TOOL)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class BuildMbaTests(unittest.TestCase):
    def test_profiles_generate_self_consistent_images(self) -> None:
        payload = bytes.fromhex("80fe0000") + bytes(range(32))
        for profile in MODULE.PROFILES.values():
            with self.subTest(slot=profile.name):
                image = MODULE.build_container(profile, payload)
                entry_offset = profile.file_offset(profile.entry)
                callback_offset = profile.file_offset(
                    profile.compatibility_address
                )

                self.assertEqual(image[:8], MODULE.MAGIC)
                self.assertEqual(len(image), profile.file_size)
                self.assertEqual(
                    struct.unpack_from("<I", image, 0x08)[0] * 2,
                    len(image),
                )
                self.assertEqual(
                    struct.unpack_from("<I", image, 0x14)[0], profile.entry
                )
                self.assertEqual(
                    struct.unpack_from("<I", image, 0x18)[0], profile.body_load
                )
                self.assertEqual(
                    image[entry_offset : entry_offset + len(payload)], payload
                )
                self.assertEqual(
                    struct.unpack_from("<2H", image, callback_offset),
                    MODULE.far_goto_words(profile.entry),
                )
                self.assertEqual(
                    struct.unpack_from("<H", image, 0x3C)[0],
                    MODULE.crc16_ccitt_false(image[:0x3C]),
                )
                self.assertNotEqual(image[0xA0:0xC0], bytes(0x20))
                self.assertNotEqual(image[0xC0:0xDC0], bytes(0xD00))
                self.assertEqual(
                    image[0xDC0:0x1000], MODULE.launcher_footer(profile)
                )

    def test_rejects_odd_and_oversized_payloads(self) -> None:
        profile = MODULE.PROFILES["SY"]
        with self.assertRaisesRegex(ValueError, "even"):
            MODULE.build_container(profile, b"\0")

        available = profile.file_offset(profile.compatibility_address) - (
            profile.file_offset(profile.entry)
        )
        with self.assertRaisesRegex(ValueError, "exceeds"):
            MODULE.build_container(profile, bytes(available + 2))


if __name__ == "__main__":
    unittest.main()
