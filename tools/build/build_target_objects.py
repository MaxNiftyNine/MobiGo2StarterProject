#!/usr/bin/env python3
"""Compile the clean-room runtime into Generalplus u'nSP object files."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path


def fail(message: str) -> "NoReturn":
    raise SystemExit(f"build_target_objects: {message}")


def run(command: list[str], *, env: dict[str, str]) -> None:
    result = subprocess.run(command, env=env, check=False)
    if result.returncode:
        fail(f"{Path(command[1]).name} failed with exit code {result.returncode}")


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    starter = root
    ide = starter / "vendor" / "generalplus" / "compiler" / "windows" / "unSPIDE_4.1.1"
    toolchain = ide / "toolchain"
    include = root / "include"
    build = root / "build" / "target"
    generated_settings = root / "build" / "clean_settings"
    generated_family_a = root / "build" / "clean_family_a"
    generated_poweroff = root / "build" / "clean_poweroff"
    generated_system_ui = root / "build" / "clean_system_ui"
    generated_font = root / "build" / "clean_font"
    subprocess.run(
        [
            sys.executable,
            str(root / "tools" / "assets" / "build_standard_settings_bundle.py"),
            str(generated_settings),
            "--prefix",
            "mobigo_clean_settings",
        ],
        check=True,
    )
    subprocess.run(
        [
            sys.executable,
            str(root / "tools" / "assets" / "build_poweroff_bundle.py"),
            str(generated_poweroff),
            "--prefix",
            "mobigo_clean_poweroff",
        ],
        check=True,
    )
    subprocess.run(
        [
            sys.executable,
            str(root / "tools" / "assets" / "build_family_a_background_bundle.py"),
            str(generated_family_a),
            "--prefix",
            "mobigo_clean_family_a",
        ],
        check=True,
    )
    subprocess.run(
        [
            sys.executable,
            str(root / "tools" / "assets" / "build_system_ui_bundle.py"),
            str(generated_system_ui),
            "--prefix",
            "mobigo_clean_system_ui",
        ],
        check=True,
    )
    subprocess.run(
        [
            sys.executable,
            str(root / "tools" / "assets" / "build_clean_font_bundle.py"),
            str(generated_font),
            "--prefix",
            "mobigo_clean_font",
        ],
        check=True,
    )
    sources = [
        root / "src" / "system_controls.c",
        root / "src" / "hardware.c",
        root / "src" / "direct_controls.c",
        root / "src" / "standard_controls.c",
        root / "src" / "input.c",
        root / "src" / "audio.c",
        root / "src" / "audio_resources.c",
        root / "src" / "resident_backend.c",
        root / "src" / "resident_input.c",
        root / "src" / "resident_keys.c",
        root / "src" / "resident_runtime.c",
        root / "src" / "resident_audio.c",
        root / "src" / "resource_bundle.c",
        root / "src" / "resource_graphics.c",
        root / "src" / "ui_family_b.c",
        root / "src" / "ui_family_b_animation.c",
        root / "src" / "settings_overlay.c",
        root / "src" / "resident_resources.c",
        root / "src" / "resident_storage.c",
        root / "src" / "touch.c",
        root / "src" / "resident_touch.c",
        root / "src" / "application.c",
        root / "examples" / "runtime_poll.c",
        root / "examples" / "resident_lifecycle.c",
        generated_settings / "mobigo_clean_settings_resources.c",
        generated_family_a / "mobigo_clean_family_a_resources.c",
        generated_poweroff / "mobigo_clean_poweroff_resources.c",
        generated_system_ui / "mobigo_clean_system_ui_resources.c",
        generated_font / "mobigo_clean_font_resources.c",
    ]

    wine = os.environ.get("MOBIGO_WINE") or shutil.which("wine")
    winepath = shutil.which("winepath")
    if not wine or not winepath:
        fail("Wine and winepath are required")
    required = [
        toolchain / "udocc.exe",
        toolchain / "xasm16.exe",
        include,
        *sources,
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        fail("required path is missing: " + missing[0])
    build.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env.setdefault("WINEDEBUG", "-all")
    env.setdefault("MVK_CONFIG_LOG_LEVEL", "0")

    requested = [toolchain, include, build, *sources]
    translated = None
    for attempt in range(3):
        result = subprocess.run(
            [winepath, "-w", *(str(path) for path in requested)],
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        if result.returncode == 0 and len(lines) == len(requested):
            translated = lines
            break
        if attempt < 2:
            time.sleep(1)
    if translated is None:
        fail("winepath could not translate the SDK paths")

    toolchain_w, include_w, build_w, *sources_w = translated
    env["WINEPATH"] = toolchain_w + (
        ";" + env["WINEPATH"] if env.get("WINEPATH") else ""
    )

    for source, source_w in zip(sources, sources_w):
        stem = source.stem
        asm_w = f"{build_w}\\{stem}.asm"
        obj_w = f"{build_w}\\{stem}.obj"
        print(f"[u'nSP C] {source.name}")
        run(
            [
                wine,
                str(toolchain / "udocc.exe"),
                "-S",
                "-O2",
                "-ffast-math",
                "-fomit-frame-pointer",
                "-funsigned-char",
                "-Wall",
                "-mglobal-var-iram",
                "-mISA=2.0",
                f"-I{include_w}",
                "-o",
                asm_w,
                source_w,
            ],
            env=env,
        )
        print(f"[u'nSP ASM] {stem}.asm")
        run(
            [
                wine,
                str(toolchain / "xasm16.exe"),
                "-t4",
                "-sr",
                "-wpop",
                f"-I{include_w}",
                "-o",
                obj_w,
                asm_w,
            ],
            env=env,
        )

    print(f"PASS objects={len(sources)} output={build}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
