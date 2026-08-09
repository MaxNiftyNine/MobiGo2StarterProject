#!/usr/bin/env python3
"""Verify HomebrewLauncher.MBA UI, catalog, and follow-up MBA launch."""

from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import tempfile

from emulator_support import ensure_nand, find_emulator


ROOT = Path(__file__).resolve().parents[2]
BUILD = ROOT / "build" / "homebrew-launcher"
STATE_BASE = 0x6420
INDEX_BASE = 0x6460
LAUNCHER_ENTRY = 0x0DFC1D
RETAIL_G1_ENTRY = 0x0E1A55


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


catalog = load_module(
    "launcher_catalog", ROOT / "examples" / "homebrew_launcher" / "catalog.py"
)
nandfs = load_module("launcher_nandfs", ROOT / "tools" / "nand" / "nandfs.py")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def word(data: bytes, base: int, address: int) -> int:
    return struct.unpack_from("<H", data, (address - base) * 2)[0]


def read_bmp(path: Path) -> tuple[int, int, set[tuple[int, int, int]], str]:
    data = path.read_bytes()
    if len(data) < 54 or data[:2] != b"BM":
        raise RuntimeError(f"not a BMP: {path}")
    offset = struct.unpack_from("<I", data, 10)[0]
    width = struct.unpack_from("<i", data, 18)[0]
    height = abs(struct.unpack_from("<i", data, 22)[0])
    bpp = struct.unpack_from("<H", data, 28)[0]
    if (width, height, bpp) != (320, 240, 32):
        raise RuntimeError(f"unexpected framebuffer format {(width, height, bpp)}")
    pixels = data[offset : offset + width * height * 4]
    colors = {
        (pixels[index + 2], pixels[index + 1], pixels[index])
        for index in range(0, len(pixels), 4)
    }
    return width, height, colors, hashlib.sha256(pixels).hexdigest()


def dark_icon_pixels(path: Path, left: int, right: int) -> int:
    data = path.read_bytes()
    offset = struct.unpack_from("<I", data, 10)[0]
    width = struct.unpack_from("<i", data, 18)[0]
    signed_height = struct.unpack_from("<i", data, 22)[0]
    height = abs(signed_height)
    count = 0
    for y in range(135, 210):
        source_y = height - 1 - y if signed_height > 0 else y
        for x in range(left, right):
            pixel = offset + (source_y * width + x) * 4
            blue, green, red = data[pixel : pixel + 3]
            if red < 80 and green < 120 and blue < 180:
                count += 1
    return count


def make_fixture(base_nand: Path) -> Path:
    fixture = BUILD / "nand.launcher-fixture.bin"
    raw = nandfs.RawNand(base_nand)
    filesystem = nandfs.MobigoFS(raw)
    with tempfile.TemporaryDirectory(prefix="launcher-nand-", dir=BUILD) as temporary:
        folder = Path(temporary) / "root"
        nandfs.cmd_extract_all(filesystem, folder)
        catalog.write_catalog(
            folder / "DEGER" / "MBASORT.LST",
            [
                catalog.CatalogEntry(
                    r"A:\BUNDLE\G1\135804G1.MBA",
                    "Hamster Highway",
                    "Touch to start",
                    "VTech",
                    1,
                ),
                catalog.CatalogEntry(
                    r"A:\BUNDLE\G2\135804G2.MBA",
                    "Puzzle Test",
                    "Touch second card",
                    "Homebrew",
                    2,
                ),
                catalog.CatalogEntry(
                    r"A:\BUNDLE\G3\135804G3.MBA",
                    "System Menu",
                ),
            ],
        )
        nandfs.cmd_repack_folder(filesystem, folder, fixture)
    rebuilt = nandfs.MobigoFS(nandfs.RawNand(fixture))
    entries = catalog.decode_catalog(rebuilt.read_file("DEGER/MBASORT.LST"))
    if len(entries) != 3 or entries[1].title != "Puzzle Test" or entries[2].title != "System Menu":
        raise RuntimeError("repacked emulator catalog did not verify")
    return fixture


def command(emulator: Path, nand: Path) -> list[str]:
    return [
        str(emulator),
        "--rom", str(ROOT / "vendor" / "firmware" / "internalrom.bin"),
        "--spi", str(ROOT / "vendor" / "firmware" / "spi.bin"),
        "--nand", str(nand),
        "--mba", str(BUILD / "HomebrewLauncher.MBA"),
        "--mba-target", "auto",
        "--mode", "fast",
        "--no-window",
    ]


def run_checked(arguments: list[str], label: str) -> str:
    result = subprocess.run(
        arguments,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
        timeout=180,
    )
    (BUILD / f"{label}.stdout.txt").write_text(result.stdout, encoding="utf-8")
    if result.returncode:
        raise RuntimeError(
            f"{label} emulator exit={result.returncode}; see "
            f"{BUILD / f'{label}.stdout.txt'}"
        )
    return result.stdout


def main() -> int:
    subprocess.run(
        [sys.executable, str(ROOT / "examples" / "homebrew_launcher" / "build.py")],
        cwd=ROOT,
        check=True,
    )
    base_nand = ensure_nand(ROOT)
    base_before = sha256(base_nand)
    fixture = make_fixture(base_nand)
    fixture_before = sha256(fixture)
    emulator = find_emulator(ROOT)

    frame_dir = BUILD / "launcher-animation-frames"
    shutil.rmtree(frame_dir, ignore_errors=True)
    frame_dir.mkdir(parents=True)
    memory_path = BUILD / "launcher-verification-state.bin"
    ui_log = BUILD / "launcher-ui.log"
    ui_output = run_checked(
        command(emulator, fixture)
        + [
            "--steps", "340000000",
            "--dump-frame-dir", str(frame_dir),
            # Avoid sampling the two-tick animation at the same phase.
            "--dump-frame-interval", "4300000",
            "--dump-memory", str(memory_path),
            "--dump-memory-base", hex(STATE_BASE),
            "--dump-memory-words", "0x400",
            "--log", "--log-file", str(ui_log),
        ],
        "launcher-ui",
    )
    memory = memory_path.read_bytes()
    status = word(memory, STATE_BASE, STATE_BASE + 4)
    entry_count = word(memory, STATE_BASE, STATE_BASE + 1)
    launch_pending = word(memory, STATE_BASE, STATE_BASE + 7)
    music_handle = word(memory, STATE_BASE, STATE_BASE + 11) | (
        word(memory, STATE_BASE, STATE_BASE + 12) << 16
    )
    music_restarts = word(memory, STATE_BASE, STATE_BASE + 13)
    frame_count = word(memory, STATE_BASE, STATE_BASE + 14)
    index_offset = (INDEX_BASE - STATE_BASE) * 2
    icon_refreshes = word(memory, STATE_BASE, STATE_BASE + 21)
    if (status, entry_count, launch_pending) != (0x8301, 3, 0):
        raise RuntimeError(
            "launcher state mismatch "
            f"status={status:#06x} count={entry_count} pending={launch_pending}"
        )
    if music_handle == 0xffffffff or music_restarts != 1 or frame_count < 2 or icon_refreshes < 1:
        raise RuntimeError(
            f"launcher music/runtime did not start handle={music_handle:#x} "
            f"restarts={music_restarts} frames={frame_count}"
        )
    if memory[index_offset : index_offset + 4] != b"HB02":
        raise RuntimeError("launcher RAM does not contain the verified HB02 catalog")
    frames = sorted(frame_dir.glob("*.bmp"))
    post_entry = [
        item for item in frames
        if int(re.search(r"_insn_(\d+)", item.name).group(1)) >= 280000000
    ]
    if len(post_entry) < 3:
        raise RuntimeError(f"launcher produced too few post-entry frames: {len(post_entry)}")
    frame_stats = [read_bmp(item) for item in post_entry]
    _, _, colors, launcher_digest = frame_stats[-1]
    animation_digests = {item[3] for item in frame_stats}
    if len(colors) < 4 or not any(blue > red and blue >= green for red, green, blue in colors):
        raise RuntimeError(f"launcher artwork is not a nonuniform blue UI: {colors}")
    if len(animation_digests) < 2:
        raise RuntimeError("launcher sine-wave artwork did not animate across captures")
    system_pixels = dark_icon_pixels(post_entry[-1], 38, 70)
    selected_pixels = dark_icon_pixels(post_entry[-1], 144, 176)
    next_pixels = dark_icon_pixels(post_entry[-1], 250, 282)
    if system_pixels != 0 or selected_pixels < 20 or next_pixels < 20:
        raise RuntimeError(
            "system item/icon visibility mismatch "
            f"system={system_pixels} selected={selected_pixels} next={next_pixels}"
        )
    if "entry=0xdfc1d" not in ui_output.lower():
        raise RuntimeError("transient launcher overlay did not report the SY entry")
    ui_lines = ui_log.read_text(encoding="utf-8").splitlines()
    launcher_at = next(
        (index for index, line in enumerate(ui_lines) if "MBA APPLICATION ENTRY entry=0xdfc1d" in line),
        None,
    )
    if launcher_at is None or not any(
        "SPU start channel=" in line and "format=0x0" in line
        for line in ui_lines[launcher_at + 1 :]
    ):
        raise RuntimeError("launcher entered but its embedded PCM8 background music never started")

    launch_log = BUILD / "launcher-followup.log"
    final_frame = BUILD / "launcher-followup.bmp"
    launch_output = run_checked(
        command(emulator, fixture)
        + [
            "--steps", "500000000",
            "--touch-event", "300000000,10000000,160,180",
            "--dump-frame", str(final_frame),
            "--log", "--log-file", str(launch_log),
        ],
        "launcher-followup",
    )
    log = launch_log.read_text(encoding="utf-8")
    entries = [int(value, 16) for value in re.findall(r"MBA APPLICATION ENTRY entry=0x([0-9a-f]+)", log)]
    if LAUNCHER_ENTRY not in entries or RETAIL_G1_ENTRY not in entries:
        raise RuntimeError(f"expected launcher and G1 entries, got {[hex(x) for x in entries]}")
    if "MBA selected target released for follow-up" not in log:
        raise RuntimeError("emulator did not release the active launcher for its selected MBA")
    if "WATCHDOG RESET" in log or "SYSTEM RESET APPLIED" in log:
        raise RuntimeError("launcher follow-up MBA reset unexpectedly")
    if "Power state: off" in launch_output:
        raise RuntimeError("launcher follow-up run powered off unexpectedly")
    _, _, final_colors, final_digest = read_bmp(final_frame)
    if final_digest == launcher_digest or len(final_colors) < 8:
        raise RuntimeError("touching the second card did not leave the launcher for the G1 title")

    if sha256(base_nand) != base_before or sha256(fixture) != fixture_before:
        raise RuntimeError("an emulator test modified its NAND input")
    print(
        "PASS HomebrewLauncher.MBA catalog=HB02 carousel=horizontal touch=1 "
        "icons=MBA-header "
        f"animated_frames={len(animation_digests)} pcm_starts={music_restarts} repeat=1 "
        f"entries={','.join(hex(x) for x in entries)} transient=1"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
