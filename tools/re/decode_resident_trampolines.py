#!/usr/bin/env python3
"""Decode the fixed MobiGo resident-service trampoline table.

The input is a little-endian memory dump beginning at word address 0x075c00.
Retail code is not copied to the report: it contains only service addresses,
far-jump targets, working names, counts, and the input hash.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path


DEFAULT_BASE = 0x075C00
DEFAULT_END = 0x075FE0
FAR_GOTO_MASK = 0xFFC0
FAR_GOTO_OPCODE = 0xFE80

WORKING_NAMES = {
    0x075C52: "register_dynamic_asset_bundle",
    0x075C54: "unregister_dynamic_asset_bundle",
    0x075C58: "create_dynamic_ui_family_b_object",
    0x075E06: "register_audio_resources",
    0x075E0A: "apply_master_volume",
    0x075E0E: "play_sound",
    0x075E1A: "get_sound_state",
    0x075E2C: "play_music",
    0x075E32: "pause_music",
    0x075E34: "resume_music",
    0x075E36: "stop_music",
    0x075E38: "get_music_state",
    0x075E3C: "set_music_repeat",
    0x075E3E: "get_music_level",
    0x075E40: "set_music_level",
    0x075E5E: "request_poweroff",
    0x075E60: "get_system_keys",
    0x075E62: "system_key_down",
    0x075E64: "system_key_pressed",
    0x075E66: "system_key_released",
    0x075E7C: "create_context",
    0x075E7E: "destroy_context",
    0x075E82: "get_context_pointer",
    0x075E84: "release_context",
    0x075E8A: "post_framework_event",
    0x075EAA: "get_volume",
    0x075EAC: "set_volume",
    0x075EB2: "get_brightness",
    0x075EB4: "set_brightness",
    0x075EC6: "get_game_keys",
    0x075EC8: "game_key_down",
    0x075ECA: "game_key_pressed",
    0x075ECC: "game_key_released",
    0x075EE0: "get_input_event_pointer",
    0x075EE2: "get_input_event_count",
    0x075EE6: "test_special_key",
    0x075EFA: "ui_runtime_init",
    0x075EFC: "ui_runtime_shutdown",
    0x075EFE: "ui_runtime_render_frame",
    0x075F00: "register_asset_bundle",
    0x075F02: "load_ui_family_a_descriptor",
    0x075F04: "init_ui_family_a_descriptor_runtime",
    0x075F06: "create_ui_family_a_object",
    0x075F08: "destroy_ui_family_a_object",
    0x075F0E: "get_ui_family_a_object",
    0x075F10: "load_ui_family_b_descriptor",
    0x075F12: "create_ui_family_b_object",
    0x075F14: "destroy_ui_family_b_object",
    0x075F18: "get_ui_family_b_object",
    0x075F1C: "bind_ui_object_control",
    0x075F2E: "get_ticks",
    0x075F30: "touch_init",
    0x075F32: "touch_shutdown",
    0x075F34: "touch_update",
    0x075F36: "touch_get_enabled",
    0x075F38: "touch_set_enabled",
    0x075F3A: "get_touch_event_pointer",
    0x075F3C: "get_touch_event_count",
    0x075F3E: "touch_clear_records",
    0x075F40: "touch_register_handler",
    0x075F42: "touch_unregister_handler",
    0x075F44: "touch_reset_handlers",
    0x075F46: "runtime_setup",
    0x075F48: "runtime_step",
    0x075F4A: "runtime_finalize",
    0x075F52: "gpio_b_bit9_hardware_init",
    0x075F82: "apply_backlight",
    0x075FA0: "storage_config",
    0x075FA2: "file_open",
    0x075FA4: "file_close",
    0x075FA6: "file_read",
    0x075FA8: "file_write",
    0x075FAA: "file_truncate_at_position",
    0x075FAC: "file_seek_absolute",
    0x075FAE: "file_size",
    0x075FB0: "file_stat",
    0x075FB2: "path_remove",
    0x075FB4: "path_exists",
    0x075FCA: "launch_mba",
    0x075FCC: "query_launch_volume",
}


def parse_int(text: str) -> int:
    return int(text, 0)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dump", type=Path)
    parser.add_argument("--base", type=parse_int, default=DEFAULT_BASE)
    parser.add_argument("--end", type=parse_int, default=DEFAULT_END)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    if args.end <= args.base or (args.end - args.base) & 1:
        parser.error("table range must contain an integral number of entries")
    data = args.dump.read_bytes()
    required = (args.end - args.base) * 2
    if len(data) < required:
        raise ValueError(
            f"{args.dump}: need at least 0x{required:x} bytes, "
            f"found 0x{len(data):x}"
        )

    words = struct.unpack_from(f"<{required // 2}H", data)
    entries = []
    active = 0
    placeholders = 0
    invalid = 0
    for word_index in range(0, len(words), 2):
        service = args.base + word_index
        opcode, low = words[word_index : word_index + 2]
        valid = opcode & FAR_GOTO_MASK == FAR_GOTO_OPCODE
        target = ((opcode & 0x3F) << 16) | low if valid else None
        placeholder = target == service if target is not None else False
        if not valid:
            invalid += 1
        elif placeholder:
            placeholders += 1
        else:
            active += 1
        item = {
            "service": service,
            "target": target,
            "active": valid and not placeholder,
        }
        if service in WORKING_NAMES:
            item["working_name"] = WORKING_NAMES[service]
        entries.append(item)

    report = {
        "schema": 1,
        "input": {
            "path": str(args.dump.resolve()),
            "sha256": hashlib.sha256(data).hexdigest(),
            "bytes": len(data),
            "base_word_address": args.base,
        },
        "encoding": {
            "mask": FAR_GOTO_MASK,
            "opcode": FAR_GOTO_OPCODE,
            "target": "((word0 & 0x3f) << 16) | word1",
        },
        "table_range": [args.base, args.end],
        "entry_count": len(entries),
        "active_count": active,
        "self_loop_placeholder_count": placeholders,
        "invalid_count": invalid,
        "entries": entries,
    }
    encoded = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
