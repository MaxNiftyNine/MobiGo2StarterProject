#!/usr/bin/env python3
"""Verify HomebrewLauncher.MBA UI, catalog, and follow-up MBA launch."""

from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import re
import struct
import subprocess
import sys
import tempfile

from emulator_support import ensure_nand, find_emulator


ROOT = Path(__file__).resolve().parents[2]
BUILD = ROOT / "build" / "homebrew-launcher"
STATE_BASE = 0x64D0
INDEX_BASE = 0x6500
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
                    r"A:\BUNDLE\G1\135804G1.MBA", "Hamster Highway.MBA"
                )
            ],
        )
        nandfs.cmd_repack_folder(filesystem, folder, fixture)
    rebuilt = nandfs.MobigoFS(nandfs.RawNand(fixture))
    entries = catalog.decode_catalog(rebuilt.read_file("DEGER/MBASORT.LST"))
    if entries != [
        catalog.CatalogEntry(r"A:\BUNDLE\G1\135804G1.MBA", "Hamster Highway.MBA")
    ]:
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

    frame = BUILD / "launcher-verification.bmp"
    memory_path = BUILD / "launcher-verification-state.bin"
    ui_output = run_checked(
        command(emulator, fixture)
        + [
            "--steps", "270000000",
            "--dump-frame", str(frame),
            "--dump-memory", str(memory_path),
            "--dump-memory-base", hex(STATE_BASE),
            "--dump-memory-words", "0x240",
        ],
        "launcher-ui",
    )
    memory = memory_path.read_bytes()
    status = word(memory, STATE_BASE, STATE_BASE + 4)
    entry_count = word(memory, STATE_BASE, STATE_BASE + 1)
    launch_pending = word(memory, STATE_BASE, STATE_BASE + 7)
    index_offset = (INDEX_BASE - STATE_BASE) * 2
    if (status, entry_count, launch_pending) != (0x8001, 1, 0):
        raise RuntimeError(
            "launcher state mismatch "
            f"status={status:#06x} count={entry_count} pending={launch_pending}"
        )
    if memory[index_offset : index_offset + 4] != b"HB01":
        raise RuntimeError("launcher RAM does not contain the verified HB01 catalog")
    _, _, colors, launcher_digest = read_bmp(frame)
    if len(colors) < 4 or not any(blue > red and blue >= green for red, green, blue in colors):
        raise RuntimeError(f"launcher artwork is not a nonuniform blue UI: {colors}")
    if "entry=0xdfc1d" not in ui_output.lower():
        raise RuntimeError("transient launcher overlay did not report the SY entry")

    launch_log = BUILD / "launcher-followup.log"
    final_frame = BUILD / "launcher-followup.bmp"
    launch_output = run_checked(
        command(emulator, fixture)
        + [
            "--steps", "500000000",
            "--key-event", "265000000,10000000,primary",
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
        raise RuntimeError("Primary did not leave the launcher framebuffer for the G1 title")

    if sha256(base_nand) != base_before or sha256(fixture) != fixture_before:
        raise RuntimeError("an emulator test modified its NAND input")
    print(
        "PASS HomebrewLauncher.MBA catalog=1 waves=light-blue "
        f"entries={','.join(hex(x) for x in entries)} transient=1"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
