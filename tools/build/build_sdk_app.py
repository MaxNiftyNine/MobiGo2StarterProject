#!/usr/bin/env python3
"""Build a MobiGo 2 SDK application and package it as a complete MBA.

The builder compiles a user-provided C entrypoint together with the portable
SDK/runtime adapters and, by default, the generated common system-UI bundle.
It uses the bundled Generalplus u'nSP compiler, assembler, linker, and linker
body. On Windows those tools run natively; on macOS and Linux they run through
Wine. The resulting G1 or SY MBA is created from scratch and never copies a
retail application body.

The direct-MBA handoff enters ``main`` without a normal C CRT initialized-data
copy. Keep mutable application state in explicitly chosen title RAM or
initialize it yourself at runtime; generated system-UI assets already use the
verified const-template + writable-bundle-copy model.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import struct
import subprocess
import sys
import time
from pathlib import Path, PureWindowsPath


SLOT_PROFILES = {
    "G1": {
        "program_base": 0x0E1A55,
        "body": "MobiGo2StarterG1.bdy",
    },
    "SY": {
        "program_base": 0x0DFC1D,
        "body": "MobiGo2StarterSY.bdy",
    },
}

CORE_SOURCES = (
    "system_controls.c",
    "input.c",
    "audio.c",
    "audio_resources.c",
    "resident_backend.c",
    "resident_input.c",
    "resident_keys.c",
    "resident_runtime.c",
    "resident_audio.c",
    "resource_bundle.c",
    "resource_graphics.c",
    "ui_family_b.c",
    "ui_family_b_animation.c",
    "settings_overlay.c",
    "resident_resources.c",
    "resident_storage.c",
    "touch.c",
    "resident_touch.c",
    "application.c",
)


def fail(message: str) -> "NoReturn":
    raise SystemExit(f"build_sdk_app: {message}")


def run(command: list[str], *, env: dict[str, str], cwd: Path | None = None) -> None:
    result = subprocess.run(command, env=env, cwd=cwd, check=False)
    if result.returncode:
        fail(f"command failed ({result.returncode}): {command[0]}")


def wine_paths(winepath: str, env: dict[str, str], paths: list[Path]) -> list[str]:
    for attempt in range(3):
        result = subprocess.run(
            [winepath, "-w", *(str(path) for path in paths)],
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        if result.returncode == 0 and len(lines) == len(paths):
            return lines
        if attempt < 2:
            time.sleep(1)
    fail("winepath could not translate homebrew build paths")


def safe_project_name(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_]", "_", value)
    if not cleaned:
        cleaned = "Homebrew"
    if cleaned[0].isdigit():
        cleaned = "HB_" + cleaned
    return cleaned[:48]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="C source containing main()")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--slot", choices=tuple(SLOT_PROFILES), default="SY")
    parser.add_argument("--name", default="HomebrewApp", help="link/output project name")
    parser.add_argument(
        "--without-system-ui",
        action="store_true",
        help="do not generate/link the common brightness/volume/off bundle",
    )
    parser.add_argument(
        "--with-clean-font",
        action="store_true",
        help="generate/link the clean-room dynamic ASCII font bundle",
    )
    parser.add_argument(
        "--extra-source",
        action="append",
        default=[],
        type=Path,
        help=(
            "additional C or u'nSP assembly source to compile/link; may be "
            "repeated. Each extra source parent is added to the include path."
        ),
    )
    parser.add_argument(
        "--install-nand",
        action="store_true",
        help="also install the MBA into a copied stitched NAND image",
    )
    parser.add_argument(
        "--nand-output",
        type=Path,
        help="output path for --install-nand (default: OUTPUT_DIR/nand.NAME.bin)",
    )
    parser.add_argument(
        "--menu-tile",
        type=Path,
        help="optional raw 0xd00-byte 64x104 indexed 4-bpp launcher tile",
    )
    parser.add_argument(
        "--palette",
        type=Path,
        help="optional raw 0x20-byte launcher RGB555 palette",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[2]
    source = args.source.expanduser().resolve()
    extra_sources = [path.expanduser().resolve() for path in args.extra_source]
    build = args.output_dir.expanduser().resolve()
    project = safe_project_name(args.name)
    profile = SLOT_PROFILES[args.slot]
    program_base = int(profile["program_base"])

    ide = root / "vendor" / "generalplus" / "compiler" / "windows" / "unSPIDE_4.1.1"
    toolchain = ide / "toolchain"
    library = ide / "library" / "CMacro" / "CMacro1232.lib"
    body = root / "vendor" / "generalplus" / "linker" / str(profile["body"])
    include = root / "include"
    generated = build / "generated"
    generated_font = build / "generated_font"

    if not source.is_file():
        fail(f"source does not exist: {source}")
    for extra_source in extra_sources:
        if not extra_source.is_file():
            fail(f"extra source does not exist: {extra_source}")
    if len({source, *extra_sources}) != 1 + len(extra_sources):
        fail("source files must be unique")
    build.mkdir(parents=True, exist_ok=True)

    sources = [root / "src" / name for name in CORE_SOURCES]
    if not args.without_system_ui:
        subprocess.run(
            [
                sys.executable,
                str(root / "tools" / "assets" / "build_system_ui_bundle.py"),
                str(generated),
                "--prefix",
                "mobigo_clean_system_ui",
            ],
            check=True,
        )
        sources.append(generated / "mobigo_clean_system_ui_resources.c")
    if args.with_clean_font:
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
        sources.append(generated_font / "mobigo_clean_font_resources.c")
    sources.extend(extra_sources)
    sources.append(source)
    extra_include_dirs = list(
        dict.fromkeys([source.parent, *(path.parent for path in extra_sources)])
    )

    native_windows = os.name == "nt"
    wine = None if native_windows else (
        os.environ.get("MOBIGO_WINE") or shutil.which("wine")
    )
    winepath = None if native_windows else shutil.which("winepath")
    if not native_windows and (not wine or not winepath):
        fail("Wine and winepath are required on macOS and Linux")

    required = [
        toolchain / "udocc.exe",
        toolchain / "xasm16.exe",
        toolchain / "xlink16.exe",
        library,
        body,
        include,
        *extra_include_dirs,
        *sources,
    ]
    if not args.without_system_ui:
        required.append(generated / "mobigo_clean_system_ui_resources.h")
    if args.with_clean_font:
        required.append(generated_font / "mobigo_clean_font_resources.h")
    for optional in (args.menu_tile, args.palette):
        if optional is not None:
            required.append(optional.expanduser().resolve())
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        fail("required path is missing: " + missing[0])

    env = os.environ.copy()
    env.setdefault("WINEDEBUG", "-all")
    env.setdefault("MVK_CONFIG_LOG_LEVEL", "0")

    requested = [root, ide, toolchain, library, body, include, build]
    if not args.without_system_ui:
        requested.append(generated)
    if args.with_clean_font:
        requested.append(generated_font)
    requested.extend(extra_include_dirs)
    requested.extend(sources)
    translated = (
        [str(path) for path in requested]
        if native_windows
        else wine_paths(str(winepath), env, requested)
    )
    index = 0
    root_w = translated[index]; index += 1
    ide_w = translated[index]; index += 1
    toolchain_w = translated[index]; index += 1
    library_w = translated[index]; index += 1
    body_w = translated[index]; index += 1
    include_w = translated[index]; index += 1
    build_w = translated[index]; index += 1
    generated_w = None
    if not args.without_system_ui:
        generated_w = translated[index]; index += 1
    generated_font_w = None
    if args.with_clean_font:
        generated_font_w = translated[index]; index += 1
    extra_include_w = translated[index : index + len(extra_include_dirs)]
    index += len(extra_include_dirs)
    sources_w = translated[index:]
    if native_windows:
        env["PATH"] = str(toolchain) + os.pathsep + env.get("PATH", "")
    else:
        env["WINEPATH"] = toolchain_w + (
            ";" + env["WINEPATH"] if env.get("WINEPATH") else ""
        )

    def tool_command(executable: Path, *arguments: str) -> list[str]:
        if native_windows:
            return [str(executable), *arguments]
        return [str(wine), str(executable), *arguments]

    object_paths: list[str] = []
    used_stems: dict[str, int] = {}
    for source_path, source_w in zip(sources, sources_w):
        stem = source_path.stem
        count = used_stems.get(stem, 0)
        used_stems[stem] = count + 1
        if count:
            stem = f"{stem}_{count}"
        asm_w = f"{build_w}\\{stem}.asm"
        obj_w = f"{build_w}\\{stem}.obj"
        object_paths.append(obj_w)
        include_args = [f"-I{include_w}"]
        if generated_w is not None:
            include_args.append(f"-I{generated_w}")
        if generated_font_w is not None:
            include_args.append(f"-I{generated_font_w}")
        include_args.extend(f"-I{directory}" for directory in extra_include_w)
        if source_path.suffix.lower() == ".c":
            print(f"[u'nSP C] {source_path.name}")
            run(
                tool_command(
                    toolchain / "udocc.exe",
                    "-S",
                    "-O2",
                    "-ffast-math",
                    "-fomit-frame-pointer",
                    "-funsigned-char",
                    "-Wall",
                    "-mglobal-var-iram",
                    "-mISA=2.0",
                    *include_args,
                    "-o",
                    asm_w,
                    source_w,
                ),
                env=env,
            )
            assembler_input = asm_w
        elif source_path.suffix.lower() in (".asm", ".s"):
            assembler_input = source_w
        else:
            fail(f"unsupported source type: {source_path}")
        print(f"[u'nSP ASM] {source_path.name}")
        run(
            tool_command(
                toolchain / "xasm16.exe",
                "-t4",
                "-sr",
                "-wpop",
                *include_args,
                "-o",
                obj_w,
                assembler_input,
            ),
            env=env,
        )

    ary = build / f"{project}.ary"
    # The resident graphics path expects generated resource data to retain the
    # Generalplus linker's section alignment even as applications add sources.
    # Align both executable and initialized-data sections for every object.
    ary_lines = [
        *(f'Obj: "{obj}"' for obj in object_paths),
        *(f'Align: CODE in "{PureWindowsPath(obj).name}" with 4'
          for obj in object_paths),
        *(f'Align: NB_DATA in "{PureWindowsPath(obj).name}" with 4'
          for obj in object_paths),
        f'Lib: "{library_w}"',
        f'PrjPath: "{root_w}\\"',
        f'LibPath: "{ide_w}\\"',
        f'LibPath: "{ide_w}\\library\\CMacro"',
        'IDE_Version: "4.1.1"',
        "",
    ]
    ary.write_text("\n".join(ary_lines), encoding="ascii")

    app_s37 = build / f"{project}.s37"
    print(f"[u'nSP LINK] {app_s37.name}")
    run(
        tool_command(
            toolchain / "xlink16.exe",
            "-as",
            f"{build_w}\\{project}.ary",
            f"{build_w}\\{project}.s37",
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
        ),
        env=env,
        cwd=build,
    )

    root_lik = root / f"{project}.lik"
    if root_lik.is_file():
        root_lik.replace(build / root_lik.name)

    linker_map = build / f"{project}.map"
    if not linker_map.exists():
        alternatives = list(build.glob("*.map"))
        if len(alternatives) != 1:
            fail("could not identify linker map")
        linker_map = alternatives[0]

    match = re.search(
        r"^_main\s+([0-9A-Fa-f]+)",
        linker_map.read_text(errors="replace"),
        re.MULTILINE,
    )
    if not match:
        fail("could not find _main in linker map")
    main_address = int(match.group(1), 16)

    app_bin = build / "app.bin"
    vector_start = program_base + 0xFFF0
    run(
        [
            sys.executable,
            str(root / "tools" / "build" / "srec_to_bin.py"),
            str(app_s37),
            str(app_bin),
            hex(program_base),
            hex(vector_start),
        ],
        env=env,
    )
    program = bytearray(app_bin.read_bytes())
    if len(program) < 4:
        fail("compiler produced an unexpectedly small payload")
    struct.pack_into(
        "<HH",
        program,
        0,
        0xFE80 | ((main_address >> 16) & 0x3F),
        main_address & 0xFFFF,
    )
    app_bin.write_bytes(program)

    mba = build / f"{project}.MBA"
    mba_command = [
        sys.executable,
        str(root / "tools" / "build" / "build_mba.py"),
        "--slot",
        args.slot,
        "--payload",
        str(app_bin),
        "--output",
        str(mba),
    ]
    if args.menu_tile is not None:
        mba_command.extend(["--menu-tile", str(args.menu_tile.expanduser().resolve())])
    if args.palette is not None:
        mba_command.extend(["--palette", str(args.palette.expanduser().resolve())])
    run(mba_command, env=env)

    nand = None
    if args.install_nand:
        source_nand = root / "vendor" / "firmware" / "nand.us-stitched.bin"
        if not source_nand.exists():
            run(
                [
                    sys.executable,
                    str(root / "tools" / "nand" / "assemble_nand.py"),
                    "--output",
                    str(source_nand),
                ],
                env=env,
            )
        nand = (
            args.nand_output.expanduser().resolve()
            if args.nand_output is not None
            else build / f"nand.{project}.bin"
        )
        nand.parent.mkdir(parents=True, exist_ok=True)
        run(
            [
                sys.executable,
                str(root / "tools" / "nand" / "install_mba.py"),
                str(source_nand),
                str(mba),
                str(nand),
                "--slot",
                args.slot,
                "--editor",
                str(root / "tools" / "nand" / "nandfs.py"),
            ],
            env=env,
        )

    (build / "entry.txt").write_text(f"0x{program_base:X}\n", encoding="ascii")
    summary = (
        f"PASS slot={args.slot} main=0x{main_address:X} "
        f"payload_bytes={len(program)} mba={mba}"
    )
    if nand is not None:
        summary += f" nand={nand}"
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
