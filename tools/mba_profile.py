#!/usr/bin/env python3
"""Inspect the generated SY/G1 metadata used by safe install workflows."""

from __future__ import annotations

import struct
from dataclasses import dataclass


MAGIC = b"bM_gbMQa"


@dataclass(frozen=True)
class MbaProfile:
    slot: str
    file_size: int
    field_0c: int
    compatibility_address: int
    entry_address: int
    body_load_address: int


PROFILES = {
    "SY": MbaProfile("SY", 0x174000, 0x5387A, 0x0F3E60, 0x0DFC1D, 0x0C8800),
    "G1": MbaProfile("G1", 0x214000, 0x3BC0B, 0x0F3E5C, 0x0E1A55, 0x0C8800),
}


def detect_mba_profile(data: bytes) -> str | None:
    """Return ``SY``/``G1`` for a complete known profile, otherwise ``None``.

    A custom printable menu title does not change the executable profile, so
    detection uses the size and all five launch fields rather than trusting the
    title string alone.
    """

    if len(data) < 0xA0 or data[:8] != MAGIC or len(data) & 1:
        raise ValueError("input does not have a valid even-sized MBA header")
    declared_words, field_0c, compatibility, entry, body_load = (
        struct.unpack_from("<5I", data, 0x08)
    )
    if declared_words != len(data) // 2:
        raise ValueError("MBA header word count does not match the file size")
    for slot, profile in PROFILES.items():
        if (
            len(data) == profile.file_size
            and field_0c == profile.field_0c
            and compatibility == profile.compatibility_address
            and entry == profile.entry_address
            and body_load == profile.body_load_address
        ):
            return slot
    return None


def require_mba_profile(
    data: bytes,
    expected_slot: str,
    *,
    allow_unverified: bool = False,
) -> str | None:
    """Reject a cross-slot or unknown MBA before a persistent installation."""

    expected = expected_slot.upper()
    if expected not in PROFILES:
        raise ValueError(f"unknown MBA slot profile: {expected_slot}")
    detected = detect_mba_profile(data)
    if detected is not None and detected != expected:
        raise ValueError(
            f"MBA is linked for {detected}, not the selected {expected} slot"
        )
    if detected is None and not allow_unverified:
        raise ValueError(
            "MBA does not match a verified SY/G1 profile; pass the explicit "
            "unverified-profile override only after independently checking its "
            "entry, load, compatibility, and size fields"
        )
    return detected
