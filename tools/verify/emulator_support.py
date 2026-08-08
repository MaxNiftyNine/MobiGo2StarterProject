"""Shared host-emulator discovery for deterministic verification scripts."""

from __future__ import annotations

import platform
import subprocess
import sys
from functools import cache
from pathlib import Path


def find_emulator(root: Path, *, build_if_missing: bool = True) -> Path:
    if platform.system() == "Windows":
        executable = root / "emulator" / "bin" / "windows" / "mobigo2_emu.exe"
        if not executable.is_file():
            raise FileNotFoundError(f"Windows emulator executable is missing: {executable}")
        return executable

    executable = root / "build" / "emulator-host" / "mobigo2_emu"
    if not executable.is_file() and build_if_missing:
        subprocess.run(
            ["bash", str(root / "tools" / "build" / "emulator_unix.sh")],
            check=True,
        )
    if not executable.is_file():
        raise FileNotFoundError(f"host emulator executable is missing: {executable}")
    return executable


@cache
def ensure_nand(root: Path) -> Path:
    """Return the verified base NAND, reconstructing it from tracked parts."""
    subprocess.run(
        [sys.executable, str(root / "tools" / "nand" / "assemble_nand.py")],
        check=True,
    )
    nand = root / "vendor" / "firmware" / "nand.us-stitched.bin"
    if not nand.is_file():
        raise FileNotFoundError(f"verified NAND image is missing: {nand}")
    return nand


def mba_overlay_arguments(root: Path, mba: Path) -> list[str]:
    """Arguments for a validated, role-aware, non-mutating MBA test boot."""
    return [
        "--nand", str(ensure_nand(root)),
        "--mba", str(mba),
        "--mba-target", "auto",
    ]
