#!/usr/bin/env python3
"""Generate the runtime bundle used to show three MBA-header icons."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "tools" / "assets"
if str(ASSETS) not in sys.path:
    sys.path.insert(0, str(ASSETS))

from build_standard_settings_bundle import (  # noqa: E402
    HEADER_WORDS, PRIMARY_TAG, SECONDARY_TAG, WordBuilder,
    c_identifier, c_words, signed_word, u32_words, words_to_bytes,
)


ICON_COUNT = 3
ICON_WIDTH = 32
ICON_HEIGHT = 64
PALETTE_WORDS = 1024
ICON_WORDS = ICON_WIDTH * ICON_HEIGHT // 8
PRIMARY_WORDS = PALETTE_WORDS + ICON_COUNT * ICON_WORDS


def build_bundle() -> list[int]:
    graph = WordBuilder()
    graph.reserve(HEADER_WORDS)
    graph.label("lookup")
    graph.reserve(ICON_COUNT * 4)
    graph.label("ui_b")
    descriptor = graph.reserve(12)
    graph.label("auto")
    graph.reserve(4)
    graph.label("modes")
    modes = graph.add(*u32_words(1), 0, 0)
    graph.label("records")
    records = graph.add(*u32_words(ICON_COUNT))
    graph.reserve(ICON_COUNT * 14)

    lookup = graph.labels["lookup"]
    for index in range(ICON_COUNT):
        graph.label(f"components_{index}")
        component = graph.add(*u32_words(1), 0, 0, 0, 0)
        graph.label(f"bitmap_{index}")
        bitmap = graph.add(0, ICON_WIDTH, ICON_HEIGHT, 0, 0, 0)
        graph.label(f"slot_{index}")
        graph.add(0, 0)
        graph.set_relative(component + 4, f"bitmap_{index}")
        entry = lookup + index * 4
        graph.set_u16(entry, (ICON_HEIGHT << 8) | ICON_WIDTH)
        graph.set_u16(entry + 1, 0)
        graph.set_u32(entry + 2, PRIMARY_TAG + PALETTE_WORDS + index * ICON_WORDS)
        graph.set_u32(bitmap + 4, entry - HEADER_WORDS)
        record = records + 2 + index * 14
        graph.words[record : record + 10] = [
            0, 0, 20,
            signed_word(-(ICON_WIDTH // 2)), ICON_WIDTH // 2,
            signed_word(-(ICON_HEIGHT // 2)), ICON_HEIGHT // 2,
            0, 0xFFFF, 0xFFFF,
        ]
        graph.set_relative(record + 10, f"components_{index}")
        graph.set_relative(record + 12, f"slot_{index}")

    graph.set_u32(0x00, 0x80000002)
    graph.set_u32(0x02, PRIMARY_TAG)
    graph.set_u32(0x04, PRIMARY_TAG + 0x200)
    graph.set_u32(0x06, SECONDARY_TAG)
    graph.set_u32(0x08, SECONDARY_TAG + 0x100)
    graph.set_u16(0x0A, ICON_COUNT)
    graph.set_relative(0x0C, "lookup")
    graph.set_relative(0x10, "ui_b")
    graph.set_u16(0x12, 0)
    graph.set_relative(0x14, "ui_b")
    graph.set_u16(0x16, 1)
    graph.set_relative(0x18, "ui_b")
    graph.set_relative(0x1A, "auto")
    graph.words[descriptor : descriptor + 12] = [
        0, 0, 0, 0, 0, 0, 0, 0x40, 0xFFFF, 0xFFFF, 0, 0,
    ]
    graph.set_relative(descriptor + 10, "modes")
    graph.set_relative(modes + 2, "records")
    return graph.words


def write_outputs(output: Path, prefix: str) -> None:
    bundle = build_bundle()
    symbol = c_identifier(prefix)
    upper = symbol.upper()
    output.mkdir(parents=True, exist_ok=True)
    (output / "bundle.bin").write_bytes(words_to_bytes(bundle))
    (output / f"{prefix}_resources.h").write_text(f"""#ifndef {upper}_RESOURCES_H
#define {upper}_RESOURCES_H
#include "mobigo_sdk/mobigo_sdk.h"
enum {{
    {upper}_BUNDLE_WORD_COUNT = {len(bundle)},
    {upper}_PRIMARY_WORD_COUNT = {PRIMARY_WORDS},
    {upper}_PALETTE_WORDS = {PALETTE_WORDS},
    {upper}_ICON_WORDS = {ICON_WORDS},
    {upper}_ICON_COUNT = {ICON_COUNT}
}};
extern const unsigned short {symbol}_bundle_template[{len(bundle)}];
void {symbol}_copy_bundle(unsigned short *destination);
mg_sdk_u16 {symbol}_register(unsigned short *bundle, unsigned short *primary);
mg_sdk_ui_handle {symbol}_create(mg_sdk_u16 dynamic_slot);
#endif
""", encoding="ascii")
    (output / f"{prefix}_resources.c").write_text(f"""#include "{prefix}_resources.h"
const unsigned short {symbol}_bundle_template[{len(bundle)}] = {{
{c_words(bundle)}
}};
void {symbol}_copy_bundle(unsigned short *destination) {{
    unsigned short index;
    for (index = 0; index < {upper}_BUNDLE_WORD_COUNT; ++index)
        destination[index] = {symbol}_bundle_template[index];
}}
mg_sdk_u16 {symbol}_register(unsigned short *bundle, unsigned short *primary) {{
    return mg_sdk_resident_register_dynamic_bundle(bundle, primary);
}}
mg_sdk_ui_handle {symbol}_create(mg_sdk_u16 dynamic_slot) {{
    return mg_sdk_ui_b_create_from_dynamic_bundle(dynamic_slot, 0);
}}
""", encoding="ascii")
    print(
        f"PASS MBA icon bundle_words={len(bundle)} primary_words={PRIMARY_WORDS} "
        f"output={output}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--prefix", default="hb_icon")
    args = parser.parse_args()
    write_outputs(args.output, args.prefix)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
