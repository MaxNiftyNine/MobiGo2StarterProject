from __future__ import annotations

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tools" / "build"))

from build_mba import PROFILES as BUILD_PROFILES, build_container
from mba_profile import PROFILES, detect_mba_profile, require_mba_profile


class MbaProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.system = build_container(
            BUILD_PROFILES["SY"], b"\x00\x00", title="Custom system title"
        )
        cls.g1 = build_container(BUILD_PROFILES["G1"], b"\x00\x00")

    def test_validator_profiles_match_the_container_builder(self) -> None:
        for slot, built in BUILD_PROFILES.items():
            checked = PROFILES[slot]
            self.assertEqual(checked.file_size, built.file_size)
            self.assertEqual(checked.field_0c, built.field_0c)
            self.assertEqual(
                checked.compatibility_address, built.compatibility_address
            )
            self.assertEqual(checked.entry_address, built.entry)
            self.assertEqual(checked.body_load_address, built.body_load)

    def test_complete_metadata_detects_profile_with_a_custom_title(self) -> None:
        self.assertEqual(detect_mba_profile(self.system), "SY")
        self.assertEqual(detect_mba_profile(self.g1), "G1")

    def test_cross_slot_is_rejected_even_with_unknown_override(self) -> None:
        with self.assertRaisesRegex(ValueError, "linked for SY"):
            require_mba_profile(self.system, "G1", allow_unverified=True)

    def test_unknown_metadata_requires_an_explicit_override(self) -> None:
        unknown = bytearray(self.system)
        unknown[0x14] ^= 1
        with self.assertRaisesRegex(ValueError, "does not match"):
            require_mba_profile(bytes(unknown), "SY")
        self.assertIsNone(
            require_mba_profile(
                bytes(unknown), "SY", allow_unverified=True
            )
        )

    def test_header_size_mismatch_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "word count"):
            detect_mba_profile(self.system[:-2])


if __name__ == "__main__":
    unittest.main()
