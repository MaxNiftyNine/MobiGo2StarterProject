#!/usr/bin/env python3
"""Build the u'nSP payload locally on macOS with the bundled Windows tools."""

from __future__ import annotations

import os
import re
import shutil
import struct
import subprocess
import sys
import time
from pathlib import Path


PROGRAM_BASE = 0x0DFC1D


def fail(message: str) -> "NoReturn":
    raise SystemExit(f"build_payload_wine: {message}")


def run(command: list[str], *, env: dict[str, str], cwd: Path | None = None) -> None:
    display = Path(command[1]).name if len(command) > 1 else Path(command[0]).name
    print(f"[Wine] {display}")
    result = subprocess.run(command, env=env, cwd=cwd, check=False)
    if result.returncode:
        fail(f"{display} failed with exit code {result.returncode}")


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    ide = root / "compiler" / "windows" / "unSPIDE_4.1.1"
    toolchain = ide / "toolchain"
    library = ide / "library" / "CMacro" / "CMacro1232.lib"
    body = root / "project" / "MobiGo2StarterSY.bdy"
    source = root / "src" / "main.c"
    build = root / "build"

    wine = os.environ.get("MOBIGO_WINE") or shutil.which("wine")
    winepath = shutil.which("winepath")
    if not wine or not winepath:
        fail(
            "Wine is required. Install it with `brew install --cask wine-stable`, "
            "then retry."
        )

    required = [
        toolchain / "udocc.exe",
        toolchain / "xasm16.exe",
        toolchain / "xlink16.exe",
        library,
        body,
        source,
    ]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        fail("required build file is missing: " + missing[0])
    build.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env.setdefault("WINEDEBUG", "-all")
    env.setdefault("MVK_CONFIG_LOG_LEVEL", "0")

    def windows_paths(paths: list[Path]) -> list[str]:
        result = None
        for attempt in range(3):
            result = subprocess.run(
                [winepath, "-w", *(str(path) for path in paths)],
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
            if not result.returncode and len(lines) == len(paths):
                return lines
            if attempt < 2:
                time.sleep(1)
        detail = result.stderr.strip() if result is not None else ""
        fail("winepath could not translate project paths" + (f": {detail}" if detail else ""))

    (
        root_w,
        ide_w,
        toolchain_w,
        library_w,
        body_w,
        source_w,
        build_w,
    ) = windows_paths([root, ide, toolchain, library, body, source, build])
    env["WINEPATH"] = toolchain_w + (
        ";" + env["WINEPATH"] if env.get("WINEPATH") else ""
    )

    main_asm = build / "main.asm"
    main_obj = build / "main.obj"
    app_s37 = build / "app.s37"
    ary = build / "MobiGo2Starter.ary"
    ary.write_text(
        "\n".join(
            [
                f'Obj: "{build_w}\\main.obj"',
                f'Lib: "{library_w}"',
                f'PrjPath: "{root_w}\\"',
                f'LibPath: "{ide_w}\\"',
                f'LibPath: "{ide_w}\\library\\CMacro"',
                'IDE_Version: "4.1.1"',
                "",
            ]
        ),
        encoding="ascii",
    )

    include = f"-I{root_w}\\src"
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
            include,
            "-o",
            f"{build_w}\\main.asm",
            source_w,
        ],
        env=env,
    )
    run(
        [
            wine,
            str(toolchain / "xasm16.exe"),
            "-t4",
            "-sr",
            "-wpop",
            include,
            "-o",
            f"{build_w}\\main.obj",
            f"{build_w}\\main.asm",
        ],
        env=env,
    )
    run(
        [
            wine,
            str(toolchain / "xlink16.exe"),
            "-as",
            f"{build_w}\\MobiGo2Starter.ary",
            f"{build_w}\\app.s37",
            "-initdata",
            "-body",
            "GPL16250VA_CS0SRAM",
            "-nobdy",
            "-bfile",
            body_w,
            "-undefined-opt",
            "__TgP190708CM",
            "-undefined-opt",
            "__TgP190708CL",
            "-undefined-opt",
            "__TgP190708M",
        ],
        env=env,
        cwd=build,
    )
    # xlink16 follows PrjPath for this small sidecar even when its main outputs
    # are in build/. Keep every generated file under build as promised.
    root_lik = root / "MobiGo2Starter.lik"
    if root_lik.is_file():
        root_lik.replace(build / root_lik.name)

    app_bin = build / "app.bin"
    vector_start = PROGRAM_BASE + 0xFFF0
    convert = subprocess.run(
        [
            sys.executable,
            str(root / "tools" / "srec_to_bin.py"),
            str(app_s37),
            str(app_bin),
            hex(PROGRAM_BASE),
            hex(vector_start),
        ],
        check=False,
    )
    if convert.returncode:
        fail("srec_to_bin.py failed")

    linker_map = build / "MobiGo2Starter.map"
    if not linker_map.is_file():
        fail(f"linker map was not produced: {linker_map}")
    match = re.search(
        r"^_main\s+([0-9A-Fa-f]+)", linker_map.read_text(errors="replace"), re.MULTILINE
    )
    if not match:
        fail("could not find _main in the linker map")
    main_address = int(match.group(1), 16)

    program = bytearray(app_bin.read_bytes())
    if len(program) < 4:
        fail("compiler produced an unexpectedly small payload")
    goto_opcode = 0xFE80 | ((main_address >> 16) & 0x3F)
    struct.pack_into("<HH", program, 0, goto_opcode, main_address & 0xFFFF)
    app_bin.write_bytes(program)
    (build / "entry.txt").write_text(f"0x{PROGRAM_BASE:X}\n", encoding="ascii")

    print(f"PASS main=0x{main_address:X} payload_bytes={len(program)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
