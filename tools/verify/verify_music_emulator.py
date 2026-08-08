#!/usr/bin/env python3
"""Verify hardware-timed melodic/percussion M + PCM8 resident playback."""

from __future__ import annotations

import re
import shutil
import struct
import subprocess
import sys
from pathlib import Path

from emulator_support import find_emulator, mba_overlay_arguments


STATE_BASE = 0x5980


def word(data: bytes, index: int) -> int:
    return struct.unpack_from("<H", data, index * 2)[0]


def u32(data: bytes, index: int) -> int:
    return word(data, index) | (word(data, index + 1) << 16)


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    starter = root
    build = root / "build" / "music_check"
    name = "MusicCheck"
    emulator = find_emulator(root)
    if build.exists():
        shutil.rmtree(build)

    subprocess.run(
        [
            sys.executable,
            str(root / "tools" / "build" / "build_sdk_app.py"),
            str(root / "examples" / "audio_music_multizone_probe.c"),
            "--output-dir", str(build),
            "--name", name,
            "--slot", "SY",
            "--without-system-ui",
        ],
        check=True,
    )

    ram = build / "music_ram.bin"
    log = build / "music_emu.log"
    subprocess.run(
        [
            str(emulator),
            "--rom", str(starter / "vendor" / "firmware" / "internalrom.bin"),
            "--spi", str(starter / "vendor" / "firmware" / "spi.bin"),
            *mba_overlay_arguments(root, build / f"{name}.MBA"),
            "--no-window",
            "--steps", "254000000",
            "--dump-memory", str(ram),
            "--dump-memory-base", hex(STATE_BASE),
            "--dump-memory-words", "0x40",
            "--log",
            "--log-file", str(log),
            "--start-logging-at", "200000000",
        ],
        check=True,
    )

    data = ram.read_bytes()
    status = word(data, 0)
    handle = u32(data, 1)
    wave_0 = u32(data, 3)
    wave_1 = u32(data, 5)
    wave_2 = u32(data, 7)
    first_state = word(data, 9)
    final_state = word(data, 10)
    frames = word(data, 11)
    stop_frame = word(data, 12)
    patch_words = word(data, 13)
    phase = word(data, 14)
    first_stop_frame = word(data, 15)
    second_first_state = word(data, 16)
    second_stop_frame = word(data, 17)
    third_first_state = word(data, 18)
    observed_wave_0 = u32(data, 19)
    observed_mode_0 = word(data, 21)
    observed_pitch_0 = u32(data, 22)
    observed_panvol_0 = word(data, 24)
    wave_3 = u32(data, 25)
    fourth_first_state = word(data, 27)
    third_stop_frame = word(data, 28)
    handles = [u32(data, 29), u32(data, 31), u32(data, 33), u32(data, 35)]

    if status != 0x7772:
        raise SystemExit(f"FAIL music status={status:#06x}, expected 0x7772")
    if handle != handles[-1]:
        raise SystemExit(
            f"FAIL final music handle={handle:#010x}, recorded={handles[-1]:#010x}"
        )
    if any((value & 0xF000FFFF) != 0x40000004 for value in handles):
        raise SystemExit(
            "FAIL music handle slot/class "
            f"handles={[hex(value) for value in handles]}"
        )
    if any(handles[index + 1] - handles[index] != 0x00010000
           for index in range(3)):
        raise SystemExit(
            "FAIL music handle generations are not consecutive: "
            f"{[hex(value) for value in handles]}"
        )
    if first_state != 2 or final_state != 0:
        raise SystemExit(
            f"FAIL music states first={first_state} final={final_state}"
        )
    if second_first_state != 2 or third_first_state != 2 or fourth_first_state != 2:
        raise SystemExit(
            "FAIL later music initial states "
            f"second={second_first_state} third={third_first_state} "
            f"fourth={fourth_first_state}, expected 2/2/2"
        )
    if not (
        1 < first_stop_frame < second_stop_frame < third_stop_frame < stop_frame <= 80
    ):
        raise SystemExit(
            "FAIL music stop frames "
            f"first={first_stop_frame} second={second_stop_frame} "
            f"third={third_stop_frame} fourth={stop_frame}"
        )
    if frames <= stop_frame:
        raise SystemExit(f"FAIL music frame count={frames}")
    if patch_words != 188 or phase != 5:
        raise SystemExit(
            f"FAIL patch_words={patch_words} phase={phase}, expected 188/5"
        )
    if (wave_1 != wave_0 + 34 or wave_2 != wave_1 + 34 or
            wave_3 != wave_2 + 34):
        raise SystemExit(
            "FAIL waveform spacing "
            f"{wave_0:#x}->{wave_1:#x}->{wave_2:#x}->{wave_3:#x}, "
            "expected +34/+34/+34 words"
        )
    if (
        observed_wave_0 < wave_0
        or observed_wave_0 >= wave_0 + 34
        or (observed_mode_0 & 0xF000) != 0x2000
        or observed_pitch_0 != 0x1D1D
        or observed_panvol_0 != 0x405A
    ):
        raise SystemExit(
            "FAIL first-zone direct SPU observation "
            f"wave={observed_wave_0:#x} mode={observed_mode_0:#x} "
            f"pitch={observed_pitch_0:#x} panvol={observed_panvol_0:#x}"
        )

    start_lines: dict[int, str] = {}
    for line in log.read_text(errors="replace").splitlines():
        if "SPU start channel=" not in line:
            continue
        match = re.search(r"wave=0x([0-9a-fA-F]+)", line)
        if match:
            wave = int(match.group(1), 16)
            if wave in (wave_0, wave_1, wave_2, wave_3):
                start_lines[wave] = line
    if set(start_lines) != {wave_0, wave_1, wave_2, wave_3}:
        raise SystemExit(
            "FAIL music SPU starts did not match all patch entries: "
            f"found={[hex(value) for value in start_lines]}"
        )

    expected = {
        wave_0: (0x1D1D, 0x405A),
        wave_1: (0x2BAB, 0x4064),
        wave_2: (0x3A3A, 0x406E),
        wave_3: (0x2464, 0x4078),
    }
    channels = []
    for wave, (pitch, panvol) in expected.items():
        line = start_lines[wave]
        fields = {
            key: int(value, 16)
            for key, value in re.findall(
                r"(wave|mode|pitch|panvol|env)=0x([0-9a-fA-F]+)",
                line,
            )
        }
        mode = fields.get("mode", -1)
        expected_mode = 0x1000 if wave == wave_3 else 0x2000
        if (mode & 0xC000) != 0 or (mode & 0x3000) != expected_mode:
            raise SystemExit(
                f"FAIL music SPU mode={mode:#06x}, "
                f"expected PCM8 mode {expected_mode:#06x}"
            )
        if fields.get("pitch") != pitch:
            raise SystemExit(
                f"FAIL wave={wave:#x} pitch={fields.get('pitch')}, expected {pitch:#x}"
            )
        if fields.get("panvol") != panvol:
            raise SystemExit(
                f"FAIL wave={wave:#x} panvol={fields.get('panvol')}, expected {panvol:#x}"
            )
        channel_match = re.search(r"SPU start channel=(\d+)", line)
        channels.append(int(channel_match.group(1)) if channel_match else -1)

    print(
        "PASS resident multi-zone music "
        f"handles={[hex(value) for value in handles]} channels={channels} "
        f"waves={wave_0:#08x}/{wave_1:#08x}/{wave_2:#08x}/{wave_3:#08x} "
        "pitches=0x1d1d/0x2bab/0x3a3a/0x2464 "
        f"states=2->0 x4 stop_frames={first_stop_frame}/"
        f"{second_stop_frame}/{third_stop_frame}/{stop_frame}"
    )
    print("PASS automatic SPU beat IRQ4 scheduling")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
