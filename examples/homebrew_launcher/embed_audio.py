#!/usr/bin/env python3
"""Turn the checked-in PCM8 binary/manifest into target C sources."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import struct


def write(source: Path, manifest_path: Path, output: Path) -> None:
    raw = source.read_bytes()
    if len(raw) & 1:
        raise ValueError("PCM8 asset must contain whole 16-bit words")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    detail = manifest["output"]
    if detail["byte_count"] != len(raw):
        raise ValueError("PCM8 manifest byte count does not match binary")
    words = struct.unpack(f"<{len(raw) // 2}H", raw)
    output.mkdir(parents=True, exist_ok=True)
    (output / "hb_music.h").write_text(
        f"""#ifndef HB_MUSIC_H
#define HB_MUSIC_H
#include "mobigo_sdk/system_controls.h"
#define HB_MUSIC_SAMPLE_RATE ((mg_sdk_u32){detail['sample_rate']}UL)
#define HB_MUSIC_SAMPLE_COUNT ((mg_sdk_u32){detail['sample_count']}UL)
#define HB_MUSIC_BYTE_COUNT ((mg_sdk_u32){detail['byte_count']}UL)
#define HB_MUSIC_WORD_COUNT {len(words)}
extern const mg_sdk_u16 hb_music_words[HB_MUSIC_WORD_COUNT];
#endif
""",
        encoding="ascii",
    )
    lines = []
    for start in range(0, len(words), 8):
        lines.append(
            "    " + ", ".join(f"0x{word:04x}" for word in words[start:start + 8]) + ","
        )
    (output / "hb_music.c").write_text(
        '#include "hb_music.h"\n'
        "const mg_sdk_u16 hb_music_words[HB_MUSIC_WORD_COUNT] = {\n"
        + "\n".join(lines)
        + "\n};\n",
        encoding="ascii",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("binary", type=Path)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    write(args.binary, args.manifest, args.output)
    print(f"PASS embedded PCM8 launcher audio output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
