#!/usr/bin/env python3
"""Verify clean const PCM8 playback through the retail resident audio path."""

from __future__ import annotations

import re
import shutil
import struct
import subprocess
import sys
from pathlib import Path


STATE_BASE = 0x59D0


def read_word(data: bytes, address: int) -> int:
    return struct.unpack_from("<H", data, (address - STATE_BASE) * 2)[0]


def read_u32(data: bytes, address: int) -> int:
    return read_word(data, address) | (read_word(data, address + 1) << 16)


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    starter = root
    build = root / "build" / "audio_check"
    name = "AudioCheck"
    emulator = starter / "build" / "emulator-macos" / "mobigo2_emu"

    if not emulator.exists():
        subprocess.run(
            [str(starter / "tools" / "build" / "emulator_macos.sh")],
            check=True,
        )
    if build.exists():
        shutil.rmtree(build)

    subprocess.run(
        [
            sys.executable,
            str(root / "tools" / "build" / "build_sdk_app.py"),
            str(root / "examples" / "audio_pcm_const_boot_test.c"),
            "--output-dir", str(build),
            "--name", name,
            "--slot", "SY",
            "--without-system-ui",
            "--install-nand",
        ],
        check=True,
    )

    ram = build / "audio_ram.bin"
    log = build / "audio_emu.log"
    subprocess.run(
        [
            str(emulator),
            "--rom", str(starter / "vendor" / "firmware" / "internalrom.bin"),
            "--spi", str(starter / "vendor" / "firmware" / "spi.bin"),
            "--nand", str(build / f"nand.{name}.bin"),
            "--no-window",
            "--steps", "245000000",
            "--dump-memory", str(ram),
            "--dump-memory-base", hex(STATE_BASE),
            "--dump-memory-words", "0x20",
            "--log",
            "--log-file", str(log),
            "--start-logging-at", "200000000",
        ],
        check=True,
    )

    data = ram.read_bytes()
    status = read_word(data, STATE_BASE + 0)
    handle = read_u32(data, STATE_BASE + 1)
    relocated_byte_address = read_u32(data, STATE_BASE + 3)
    waveform_word_address = read_u32(data, STATE_BASE + 5)
    frames = read_word(data, STATE_BASE + 7)

    if status != 0x7722:
        raise SystemExit(f"FAIL audio status={status:#06x}, expected 0x7722")
    if handle != 0x40000000:
        raise SystemExit(
            f"FAIL audio handle={handle:#010x}, expected 0x40000000"
        )
    if relocated_byte_address != waveform_word_address * 2:
        raise SystemExit(
            "FAIL audio relocation "
            f"byte={relocated_byte_address:#010x} "
            f"wave_word={waveform_word_address:#010x}"
        )
    if frames <= 10:
        raise SystemExit(f"FAIL audio frame loop count={frames}")

    start_line = None
    for line in log.read_text(errors="replace").splitlines():
        if "SPU start channel=0" not in line:
            continue
        match = re.search(r"wave=0x([0-9a-fA-F]+)", line)
        if match and int(match.group(1), 16) == waveform_word_address:
            start_line = line
            break
    if start_line is None:
        raise SystemExit(
            "FAIL audio no SPU channel-0 start matched "
            f"wave={waveform_word_address:#x}"
        )

    fields = {
        key: int(value, 16)
        for key, value in re.findall(
            r"(wave|mode|pitch|panvol|env)=0x([0-9a-fA-F]+)",
            start_line,
        )
    }
    if fields.get("wave") != waveform_word_address:
        raise SystemExit(
            "FAIL audio SPU wave address "
            f"logged={fields.get('wave')} expected={waveform_word_address:#x}"
        )
    mode = fields.get("mode", -1)
    if (mode & 0xC000) != 0 or (mode & 0x3000) != 0x1000:
        raise SystemExit(
            f"FAIL audio SPU mode={mode:#06x}, expected one-shot 8-bit PCM"
        )
    if fields.get("pitch") != 0x1D1D:
        raise SystemExit(
            f"FAIL audio pitch={fields.get('pitch')}, expected 0x1d1d"
        )
    if fields.get("panvol") != 0x407F or fields.get("env") != 0x007F:
        raise SystemExit(f"FAIL audio mixer fields: {start_line}")

    print(
        "PASS resident PCM8 "
        f"handle={handle:#010x} wave={waveform_word_address:#08x} "
        f"relocated_byte={relocated_byte_address:#08x} "
        f"mode={mode:#06x} pitch=0x1d1d frames={frames}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
