#!/usr/bin/env python3
"""Build a complete MobiGo 2 MBA container without a source MBA."""

from __future__ import annotations

import argparse
import hashlib
import struct
from dataclasses import dataclass
from pathlib import Path


MAGIC = b"bM_gbMQa"
HEADER_SIZE = 0x1000
HEADER_WORDS = HEADER_SIZE // 2
TILE_WIDTH = 64
TILE_HEIGHT = 104
TILE_BYTES = TILE_WIDTH * TILE_HEIGHT // 2
LAUNCHER_FOOTER_OFFSET = 0x0DC0
LAUNCHER_FOOTER_SIZE = HEADER_SIZE - LAUNCHER_FOOTER_OFFSET


@dataclass(frozen=True)
class SlotProfile:
    name: str
    file_size: int
    field_0c: int
    compatibility_address: int
    entry: int
    body_load: int
    field_1c: int
    field_20: int
    field_24: int
    field_28: int
    role: str
    launcher_footer_words: tuple[tuple[int, int], ...]

    @property
    def runtime_base(self) -> int:
        return self.body_load - HEADER_WORDS

    def file_offset(self, word_address: int) -> int:
        return (word_address - self.runtime_base) * 2


# These are complete slot profiles recovered from the cross-sample format
# analysis. They are format metadata, not copied header or body bytes.
PROFILES = {
    "G1": SlotProfile(
        "G1", 0x214000, 0x3BC0B, 0x0F3E5C, 0x0E1A55, 0x0C8800,
        0x0000FFFF, 0x0000FFFF, 0x00280642, 0x000006E0, "MGB_G1",
        (
            (0xDC0, 0x000C8000), (0xDC4, 0x003FD000),
            (0xDC8, 0x00075C00), (0xDCC, 0x00075FE0),
            (0xDD0, 0x000006EC), (0xDD4, 0x00000756),
            (0xDD8, 0xFFFFFFFF), (0xDDC, 0xFFFFFFFF),
            (0xDE0, 0xFFFFFFFF), (0xDE4, 0x00FFFFFF),
            (0xE6C, 0xFFFFFFC0),
            (0xE70, 0xFFFFFFFF), (0xE74, 0xFFFFFFFF),
            (0xE78, 0xFFFFFFFF), (0xE7C, 0xFFFFFFFF),
            (0xE80, 0xFFFFFFFF), (0xE84, 0xFFFFFFFF),
            (0xE88, 0xFFFFFFFF), (0xE8C, 0xFFFFFFFF),
            (0xE90, 0xFFFFFFFF), (0xE94, 0xFFFFFFFF),
            (0xE98, 0xFFFFFFFF), (0xE9C, 0xFFFFFFFF),
            (0xEA0, 0x00000003),
        ),
    ),
    "SY": SlotProfile(
        "SY", 0x174000, 0x5387A, 0x0F3E60, 0x0DFC1D, 0x0C8800,
        0x0000FFFF, 0x0000FFFF, 0x00280642, 0x000006E0, "MGB_SYS",
        (
            (0xDC0, 0x000C8000), (0xDC4, 0x003FD000),
            (0xDC8, 0x00075C00), (0xDCC, 0x00075FE0),
            (0xDD0, 0x000006EC), (0xDD4, 0x00000756),
            (0xDD8, 0xFFFFFFFF), (0xDDC, 0xFFFFFFFF),
            (0xDE0, 0xFFFFFFFF), (0xDE4, 0x00003FFF),
            (0xE7C, 0xF0000000),
            (0xE80, 0xFFFFFFFF), (0xE84, 0xFFFFFFFF),
            (0xE88, 0xFFFFFFFF), (0xE8C, 0xFFFFFFFF),
            (0xE90, 0xFFFFFFFF), (0xE94, 0xFFFFFFFF),
            (0xE98, 0xFFFFFFFF), (0xE9C, 0xFFFFFFFF),
            (0xEA0, 0x00000003),
        ),
    ),
}


def crc16_ccitt_false(data: bytes | bytearray) -> int:
    crc = 0xFFFF
    for value in data:
        crc ^= value << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (
                crc << 1
            ) & 0xFFFF
    return crc


def rgb555(red: int, green: int, blue: int, *, transparent: bool = False) -> int:
    value = ((red * 31 // 255) << 10) | ((green * 31 // 255) << 5) | (
        blue * 31 // 255
    )
    return value | (0x8000 if transparent else 0)


def default_palette() -> bytes:
    colors = [
        rgb555(0, 0, 0, transparent=True),
        rgb555(8, 20, 48),
        rgb555(255, 255, 255),
        rgb555(44, 214, 255),
        rgb555(255, 189, 46),
        rgb555(78, 236, 121),
    ] + [rgb555(0, 0, 0)] * 10
    return struct.pack("<16H", *colors)


def default_menu_tile() -> bytes:
    pixels = bytearray(TILE_WIDTH * TILE_HEIGHT)

    def rectangle(x0: int, y0: int, x1: int, y1: int, color: int) -> None:
        for y in range(max(0, y0), min(TILE_HEIGHT, y1)):
            start = y * TILE_WIDTH + max(0, x0)
            end = y * TILE_WIDTH + min(TILE_WIDTH, x1)
            pixels[start:end] = bytes([color]) * max(0, end - start)

    # A deterministic, original "HB" launcher tile.
    rectangle(4, 4, 60, 100, 1)
    rectangle(4, 4, 60, 7, 3)
    rectangle(4, 97, 60, 100, 3)
    rectangle(4, 4, 7, 100, 3)
    rectangle(57, 4, 60, 100, 3)

    # H
    rectangle(14, 13, 21, 45, 2)
    rectangle(43, 13, 50, 45, 2)
    rectangle(21, 26, 43, 33, 2)

    # B
    rectangle(14, 55, 21, 91, 4)
    rectangle(21, 55, 43, 62, 4)
    rectangle(21, 69, 43, 76, 4)
    rectangle(21, 84, 43, 91, 4)
    rectangle(42, 61, 49, 70, 4)
    rectangle(42, 75, 49, 85, 4)

    packed = bytearray(TILE_BYTES)
    for offset in range(0, len(pixels), 2):
        packed[offset // 2] = (pixels[offset] << 4) | pixels[offset + 1]
    return bytes(packed)


def launcher_footer(profile: SlotProfile) -> bytes:
    footer = bytearray(LAUNCHER_FOOTER_SIZE)
    for absolute_offset, value in profile.launcher_footer_words:
        if not (
            LAUNCHER_FOOTER_OFFSET
            <= absolute_offset
            <= HEADER_SIZE - 4
        ):
            raise ValueError("slot profile has a launcher-footer word out of range")
        struct.pack_into(
            "<I", footer, absolute_offset - LAUNCHER_FOOTER_OFFSET, value
        )
    return bytes(footer)


def far_goto_words(target: int) -> tuple[int, int]:
    return 0xFE80 | ((target >> 16) & 0x3F), target & 0xFFFF


def build_container(
    profile: SlotProfile,
    payload: bytes,
    *,
    title: str | None = None,
    palette: bytes | None = None,
    menu_tile: bytes | None = None,
) -> bytes:
    if not payload:
        raise ValueError("payload is empty")
    if len(payload) & 1:
        raise ValueError("payload length must be even (unSP words are 16-bit)")

    title_text = profile.role if title is None else title
    try:
        title_bytes = title_text.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError("header title must be ASCII") from exc
    if len(title_bytes) > 31:
        raise ValueError("header title must fit in 31 ASCII bytes plus NUL")

    palette_bytes = default_palette() if palette is None else palette
    tile_bytes = default_menu_tile() if menu_tile is None else menu_tile
    if len(palette_bytes) != 0x20:
        raise ValueError("palette must be exactly 0x20 bytes (16 RGB555 words)")
    if len(tile_bytes) != TILE_BYTES:
        raise ValueError(
            f"menu tile must be exactly {TILE_BYTES:#x} bytes "
            f"({TILE_WIDTH}x{TILE_HEIGHT} indexed 4-bpp)"
        )

    entry_offset = profile.file_offset(profile.entry)
    compatibility_offset = profile.file_offset(profile.compatibility_address)
    if not (HEADER_SIZE <= entry_offset < compatibility_offset):
        raise ValueError("slot profile has an invalid entry/compatibility layout")
    if entry_offset + len(payload) > compatibility_offset:
        available = compatibility_offset - entry_offset
        raise ValueError(
            f"payload exceeds the {profile.name} executable window "
            f"({len(payload)} > {available} bytes)"
        )
    if compatibility_offset + 4 > profile.file_size:
        raise ValueError("slot profile compatibility address is outside the image")

    image = bytearray(profile.file_size)
    image[:8] = MAGIC
    struct.pack_into(
        "<9I",
        image,
        0x08,
        profile.file_size // 2,
        profile.field_0c,
        profile.compatibility_address,
        profile.entry,
        profile.body_load,
        profile.field_1c,
        profile.field_20,
        profile.field_24,
        profile.field_28,
    )
    image[0x80 : 0x80 + len(title_bytes)] = title_bytes
    image[0xA0:0xC0] = palette_bytes
    image[0xC0:LAUNCHER_FOOTER_OFFSET] = tile_bytes
    image[LAUNCHER_FOOTER_OFFSET:HEADER_SIZE] = launcher_footer(profile)
    image[entry_offset : entry_offset + len(payload)] = payload

    # In the G1/SY profiles, field 0x10 is address-like. Earlier launch
    # research treated it as the next protected callback. Supply original
    # homebrew code there instead of leaving the address backed by empty data.
    struct.pack_into(
        "<HH",
        image,
        compatibility_offset,
        *far_goto_words(profile.entry),
    )

    struct.pack_into("<H", image, 0x3C, crc16_ccitt_false(image[:0x3C]))
    return bytes(image)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--slot", choices=tuple(PROFILES), default="SY")
    parser.add_argument("--payload", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--title",
        help="32-byte header role/title (default: slot-compatible MGB_SYS or MGB_G1)",
    )
    parser.add_argument(
        "--palette",
        type=Path,
        help="optional raw 0x20-byte little-endian RGB555 palette",
    )
    parser.add_argument(
        "--menu-tile",
        type=Path,
        help="optional raw 0xd00-byte 64x104 indexed 4-bpp visible tile",
    )
    args = parser.parse_args()

    payload_path = args.payload.expanduser().resolve()
    output_path = args.output.expanduser().resolve()
    if output_path == payload_path:
        parser.error("output must not overwrite the payload")
    if not payload_path.is_file():
        parser.error(f"payload does not exist: {payload_path}")

    def optional_bytes(path: Path | None) -> bytes | None:
        return None if path is None else path.expanduser().resolve().read_bytes()

    profile = PROFILES[args.slot]
    try:
        image = build_container(
            profile,
            payload_path.read_bytes(),
            title=args.title,
            palette=optional_bytes(args.palette),
            menu_tile=optional_bytes(args.menu_tile),
        )
    except (OSError, ValueError) as exc:
        parser.error(str(exc))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(image)
    check = output_path.read_bytes()
    if check != image:
        raise SystemExit("output read-back verification failed")

    entry_offset = profile.file_offset(profile.entry)
    compatibility_offset = profile.file_offset(profile.compatibility_address)
    crc = struct.unpack_from("<H", image, 0x3C)[0]
    print("PASS generated complete MBA without a source container")
    print(
        f"PASS {profile.name} base={profile.runtime_base:#x} "
        f"load={profile.body_load:#x} entry={profile.entry:#x} "
        f"entry_offset={entry_offset:#x}"
    )
    print(
        f"PASS payload={len(payload_path.read_bytes())} bytes "
        f"window={compatibility_offset - entry_offset} bytes "
        f"file={len(image)} bytes CRC={crc:#06x}"
    )
    print(f"Wrote {output_path}")
    print(f"SHA-256 {hashlib.sha256(image).hexdigest()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
