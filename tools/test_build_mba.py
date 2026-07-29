#!/usr/bin/env python3
"""Unit tests for the from-scratch MBA generator."""

from __future__ import annotations

import struct
import unittest

import build_mba


class BuildMbaTests(unittest.TestCase):
    def test_profiles_generate_self_consistent_images(self) -> None:
        payload = bytes.fromhex("80fe0000") + bytes(range(32))
        for profile in build_mba.PROFILES.values():
            with self.subTest(slot=profile.name):
                image = build_mba.build_container(profile, payload)
                entry_offset = profile.file_offset(profile.entry)
                callback_offset = profile.file_offset(
                    profile.compatibility_address
                )
                self.assertEqual(image[:8], build_mba.MAGIC)
                self.assertEqual(len(image), profile.file_size)
                self.assertEqual(
                    struct.unpack_from("<I", image, 0x08)[0] * 2, len(image)
                )
                self.assertEqual(
                    struct.unpack_from("<I", image, 0x14)[0], profile.entry
                )
                self.assertEqual(
                    struct.unpack_from("<I", image, 0x18)[0], profile.body_load
                )
                self.assertEqual(image[entry_offset : entry_offset + len(payload)], payload)
                self.assertEqual(
                    struct.unpack_from("<2H", image, callback_offset),
                    build_mba.far_goto_words(profile.entry),
                )
                self.assertEqual(
                    struct.unpack_from("<H", image, 0x3C)[0],
                    build_mba.crc16_ccitt_false(image[:0x3C]),
                )
                self.assertNotEqual(image[0xA0:0xC0], bytes(0x20))
                self.assertNotEqual(image[0xC0:0xDC0], bytes(0xD00))
                self.assertEqual(
                    image[0xDC0:0x1000],
                    build_mba.launcher_footer(profile),
                )

    def test_rejects_odd_and_oversized_payloads(self) -> None:
        profile = build_mba.PROFILES["SY"]
        with self.assertRaisesRegex(ValueError, "even"):
            build_mba.build_container(profile, b"\0")
        available = profile.file_offset(profile.compatibility_address) - (
            profile.file_offset(profile.entry)
        )
        with self.assertRaisesRegex(ValueError, "exceeds"):
            build_mba.build_container(profile, bytes(available + 2))


if __name__ == "__main__":
    unittest.main()
