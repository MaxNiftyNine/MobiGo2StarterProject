#!/usr/bin/env python3
"""Canonical cross-platform build, run, test, and environment command.

Project settings live in ``mobigo.project.json`` at the repository root. New
projects target the SY system-application profile. The legacy G1 replacement
profile is available only through an explicit configuration or command-line
override.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import NoReturn


TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from mba_profile import PROFILES as MBA_PROFILES, require_mba_profile


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "mobigo.project.json"
FIRMWARE = ROOT / "vendor" / "firmware"
BUILD = ROOT / "build"

TARGETS = {
    "system": "SY",
    "sy": "SY",
    "game1": "G1",
    "g1": "G1",
}

QUICK_TEST_TARGETS = (
    "test",
    "usb-test",
    "target-check",
    "emulator-test",
)

# A stock Windows Python installation does not include Make. Keep its normal
# test command useful, but name the missing coverage and never treat this
# bounded baseline as the full release suite.
WINDOWS_NO_MAKE_TEST_SCRIPTS = (
    ("-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"),
    (
        "-m", "unittest", "discover", "-s", "tools/usb",
        "-p", "test_*.py",
    ),
    ("tools/build/build_target_objects.py",),
    ("tools/verify/verify_homebrew_input_emulator.py",),
)


def fail(message: str) -> NoReturn:
    raise SystemExit(f"mobigo: {message}")


def run(command: list[str], *, cwd: Path = ROOT) -> None:
    printable = " ".join(command)
    print(f"+ {printable}")
    result = subprocess.run(command, cwd=cwd, check=False)
    if result.returncode:
        fail(f"command failed with status {result.returncode}: {command[0]}")


def python_command(*arguments: str | Path) -> list[str]:
    return [sys.executable, *(str(argument) for argument in arguments)]


def resolve_project_path(value: str, field: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        fail(f"{field} must be relative to the project root")
    resolved = (ROOT / path).resolve()
    try:
        resolved.relative_to(ROOT.resolve())
    except ValueError:
        fail(f"{field} escapes the project root: {value}")
    return resolved


@dataclass(frozen=True)
class Project:
    name: str
    source: Path
    target: str
    system_ui: bool
    clean_font: bool
    extra_sources: tuple[Path, ...]
    menu_tile: Path | None
    palette: Path | None

    @property
    def slot(self) -> str:
        return TARGETS[self.target]

    @property
    def mba(self) -> Path:
        return BUILD / f"{self.name}.MBA"


def load_project(target_override: str | None = None) -> Project:
    if not CONFIG_PATH.is_file():
        fail(f"missing project configuration: {CONFIG_PATH}")
    try:
        raw = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        fail(f"cannot read {CONFIG_PATH.name}: {error}")
    if not isinstance(raw, dict):
        fail(f"{CONFIG_PATH.name} must contain a JSON object")

    allowed = {
        "$schema",
        "name", "source", "target", "system_ui", "clean_font",
        "extra_sources", "menu_tile", "palette",
    }
    unknown = sorted(set(raw) - allowed)
    if unknown:
        fail(f"unknown {CONFIG_PATH.name} field: {unknown[0]}")

    name = raw.get("name", "MobiGo2Starter")
    source_value = raw.get("source", "app/main.c")
    target = (target_override or raw.get("target", "system")).lower()
    system_ui = raw.get("system_ui", True)
    clean_font = raw.get("clean_font", False)
    extra_values = raw.get("extra_sources", [])
    if not isinstance(name, str) or not re.fullmatch(
        r"[A-Za-z_][A-Za-z0-9_]{0,47}", name
    ):
        fail("name must be a C-style identifier of at most 48 characters")
    if not isinstance(source_value, str):
        fail("source must be a string")
    if target not in TARGETS:
        fail("target must be 'system' or the explicit legacy target 'game1'")
    if not isinstance(system_ui, bool) or not isinstance(clean_font, bool):
        fail("system_ui and clean_font must be true or false")
    if not isinstance(extra_values, list) or not all(
        isinstance(value, str) for value in extra_values
    ):
        fail("extra_sources must be a list of project-relative strings")

    def optional_path(field: str) -> Path | None:
        value = raw.get(field)
        if value is None:
            return None
        if not isinstance(value, str):
            fail(f"{field} must be a project-relative string or null")
        return resolve_project_path(value, field)

    project = Project(
        name=name.strip(),
        source=resolve_project_path(source_value, "source"),
        target=target,
        system_ui=system_ui,
        clean_font=clean_font,
        extra_sources=tuple(
            resolve_project_path(value, "extra_sources") for value in extra_values
        ),
        menu_tile=optional_path("menu_tile"),
        palette=optional_path("palette"),
    )
    required = [project.source, *project.extra_sources]
    if project.menu_tile is not None:
        required.append(project.menu_tile)
    if project.palette is not None:
        required.append(project.palette)
    missing = [path for path in required if not path.is_file()]
    if missing:
        fail(f"configured file does not exist: {missing[0]}")
    return project


def ensure_nand() -> Path:
    nand = FIRMWARE / "nand.us-stitched.bin"
    run(python_command(ROOT / "tools" / "nand" / "assemble_nand.py"))
    return nand


def build_project(project: Project, *, install_nand: bool = False) -> Path:
    BUILD.mkdir(parents=True, exist_ok=True)
    command = python_command(
        ROOT / "tools" / "build" / "build_sdk_app.py",
        project.source,
        "--output-dir", BUILD,
        "--name", project.name,
        "--slot", project.slot,
    )
    if not project.system_ui:
        command.append("--without-system-ui")
    if project.clean_font:
        command.append("--with-clean-font")
    for source in project.extra_sources:
        command.extend(("--extra-source", str(source)))
    if project.menu_tile is not None:
        command.extend(("--menu-tile", str(project.menu_tile)))
    if project.palette is not None:
        command.extend(("--palette", str(project.palette)))
    if install_nand:
        command.extend(
            (
                "--install-nand",
                "--nand-output", str(BUILD / "nand.edited.bin"),
            )
        )
    run(command)
    if not project.mba.is_file():
        fail(f"builder did not create the expected MBA: {project.mba}")
    return project.mba


def emulator_supports(executable: Path, option: str) -> bool:
    try:
        result = subprocess.run(
            [str(executable), "--help"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return result.returncode == 0 and option in (result.stdout + result.stderr)


def emulator_build_is_stale(executable: Path) -> bool:
    """Return true when a Unix host emulator predates its build inputs."""

    if not executable.is_file():
        return True
    built_at = executable.stat().st_mtime_ns
    inputs = [ROOT / "emulator" / "CMakeLists.txt"]
    inputs.extend((ROOT / "emulator" / "src").rglob("*"))
    return any(
        path.is_file() and path.stat().st_mtime_ns > built_at
        for path in inputs
    )


def host_emulator(*, run_tests: bool = False) -> Path:
    system = platform.system()
    if system == "Windows":
        executable = ROOT / "emulator" / "bin" / "windows" / "mobigo2_emu.exe"
        if not executable.is_file():
            fail(
                "the Windows emulator is missing; see docs/start/install.md "
                "for the source-build prerequisites"
            )
        return executable

    executable = BUILD / "emulator-host" / "mobigo2_emu"
    if emulator_build_is_stale(executable) or run_tests:
        command = [
            "bash", str(ROOT / "tools" / "build" / "emulator_unix.sh")
        ]
        if run_tests:
            command.append("--test")
        run(command)
    return executable


def install_nand_copy(project: Project, mba: Path) -> Path:
    source_nand = ensure_nand()
    output = BUILD / "nand.edited.bin"
    run(
        python_command(
            ROOT / "tools" / "nand" / "install_mba.py",
            source_nand,
            mba,
            output,
            "--slot", project.slot,
            "--editor", ROOT / "tools" / "nand" / "nandfs.py",
        )
    )
    return output


def validate_project_mba(project: Project, mba: Path) -> None:
    """Reject an invalid or cross-target artifact before emulation."""

    try:
        require_mba_profile(mba.read_bytes(), project.slot)
    except (OSError, ValueError) as error:
        fail(
            f"MBA does not match configured {project.slot} target: {error}; "
            "rebuild it without --no-build"
        )


def run_emulator(
    project: Project,
    mba: Path,
    *,
    mode: str,
    audio: bool,
) -> None:
    validate_project_mba(project, mba)
    emulator = host_emulator()
    nand = ensure_nand()
    command = [
        str(emulator),
        "--rom", str(FIRMWARE / "internalrom.bin"),
        "--spi", str(FIRMWARE / "spi.bin"),
        "--nand", str(nand),
    ]

    # New emulators can select the correct application role from the MBA header,
    # apply it only in memory, and open the window on the observed entry event.
    # The fallback keeps older distributed Windows builds usable without ever
    # cross-installing a system MBA into G1.
    if emulator_supports(emulator, "--mba-target"):
        command.extend(
            (
                "--mba", str(mba),
                "--mba-target", "auto",
                "--open-window-on-mba",
                "--mode", mode,
            )
        )
    else:
        print(
            "NOTE emulator predates transient role-aware MBA loading; "
            "creating a verified copied NAND instead."
        )
        edited = install_nand_copy(project, mba)
        command[command.index(str(nand))] = str(edited)
        command.extend(("--open-window-at", "220000000"))
        if mode == "fast":
            command.extend(("--no-cap", "--max-present-hz", "30"))
    if audio:
        command.append("--audio")
    run(command)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def doctor(*, as_json: bool = False) -> int:
    checks: list[dict[str, object]] = []

    def check(name: str, ok: bool, detail: str, required: bool = True) -> None:
        checks.append(
            {"name": name, "ok": ok, "required": required, "detail": detail}
        )

    check(
        "python",
        sys.version_info >= (3, 10),
        f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
    )
    try:
        project = load_project()
        check("project", True, f"{project.name} ({project.target})")
    except SystemExit as error:
        check("project", False, str(error))
    for name, size, expected in (
        (
            "internalrom.bin", 131_072,
            "883e2d2111bf978af1b98fcf34f577c46739da8778c1cec592be79a6f6b4d5d5",
        ),
        (
            "spi.bin", 2_097_152,
            "13c8b101afe2e04cccdc0e42d3134d2d06657057d8d6f6a84954dce4d6c230d3",
        ),
    ):
        path = FIRMWARE / name
        ok = path.is_file() and path.stat().st_size == size
        if ok:
            ok = file_sha256(path) == expected
        check(name, ok, "present and verified" if ok else "missing or hash mismatch")

    assembled_nand = FIRMWARE / "nand.us-stitched.bin"
    nand_parts = (
        (FIRMWARE / "nand.us-stitched.bin.part00", 94_371_840),
        (FIRMWARE / "nand.us-stitched.bin.part01", 44_040_192),
    )
    if assembled_nand.is_file():
        nand_ok = (
            assembled_nand.stat().st_size == 138_412_032
            and file_sha256(assembled_nand)
            == "66e686225f709e07ca0d76b78b82374cb6fd27296c7a3d8b98c765da66442e7a"
        )
        nand_detail = (
            "assembled image verified" if nand_ok
            else "assembled image has a size/hash mismatch"
        )
    else:
        nand_ok = all(
            path.is_file() and path.stat().st_size == size
            for path, size in nand_parts
        )
        nand_detail = (
            "tracked parts ready for verified assembly" if nand_ok
            else "assembled image absent and one or more tracked parts are invalid"
        )
    check("NAND firmware", nand_ok, nand_detail)

    toolchain = (
        ROOT / "vendor" / "generalplus" / "compiler" / "windows"
        / "unSPIDE_4.1.1" / "toolchain"
    )
    for executable in ("udocc.exe", "xasm16.exe", "xlink16.exe"):
        path = toolchain / executable
        check(executable, path.is_file(), str(path.relative_to(ROOT)))
    compiler_library = (
        ROOT / "vendor" / "generalplus" / "compiler" / "windows"
        / "unSPIDE_4.1.1" / "library" / "CMacro" / "CMacro1232.lib"
    )
    check(
        "CMacro1232.lib",
        compiler_library.is_file(),
        str(compiler_library.relative_to(ROOT)),
    )
    linker_profiles = (
        ROOT / "vendor" / "generalplus" / "linker" / "MobiGo2StarterSY.bdy",
        ROOT / "vendor" / "generalplus" / "linker" / "MobiGo2StarterG1.bdy",
    )
    check(
        "linker profiles",
        all(path.is_file() for path in linker_profiles),
        ", ".join(str(path.relative_to(ROOT)) for path in linker_profiles),
    )

    if os.name != "nt":
        check("wine", shutil.which("wine") is not None, shutil.which("wine") or "not found")
        check(
            "winepath",
            shutil.which("winepath") is not None,
            shutil.which("winepath") or "not found",
        )
        check("cmake", shutil.which("cmake") is not None, shutil.which("cmake") or "not found")
        check(
            "pkg-config SDL2",
            subprocess.run(
                ["pkg-config", "--exists", "sdl2"], check=False
            ).returncode == 0 if shutil.which("pkg-config") else False,
            "needed only when rebuilding the emulator",
        )
    else:
        executable = ROOT / "emulator" / "bin" / "windows" / "mobigo2_emu.exe"
        check("Windows emulator", executable.is_file(), str(executable.relative_to(ROOT)))
        for runtime in (
            "SDL2.dll",
            "libgcc_s_seh-1.dll",
            "libstdc++-6.dll",
            "libwinpthread-1.dll",
        ):
            path = executable.parent / runtime
            check(
                f"Windows emulator {runtime}",
                path.is_file(),
                str(path.relative_to(ROOT)),
            )
        if executable.is_file():
            current_options = (
                emulator_supports(executable, "--mba-target")
                and emulator_supports(executable, "--mode")
                and emulator_supports(executable, "--no-window")
            )
            check(
                "Windows emulator capabilities",
                current_options,
                "current CLI available" if current_options
                else "startup or CLI probe failed",
            )

    failed = [item for item in checks if item["required"] and not item["ok"]]
    if as_json:
        print(json.dumps({"ok": not failed, "checks": checks}, indent=2))
    else:
        for item in checks:
            status = "PASS" if item["ok"] else "FAIL"
            print(f"{status:4} {item['name']}: {item['detail']}")
        print("Environment ready." if not failed else f"{len(failed)} required check(s) failed.")
    return 0 if not failed else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor_parser = subparsers.add_parser("doctor", help="check required tools and files")
    doctor_parser.add_argument("--json", action="store_true", help="emit machine-readable results")

    build_parser = subparsers.add_parser("build", help="compile and package the configured MBA")
    build_parser.add_argument(
        "--target", choices=("system", "game1"),
        help="override the configured target; game1 is a legacy opt-in profile",
    )
    build_parser.add_argument(
        "--nand", action="store_true",
        help="also create build/nand.edited.bin (normally runtime overlay is faster)",
    )

    run_parser = subparsers.add_parser("run", help="build and launch in Emulator2")
    run_parser.add_argument("--target", choices=("system", "game1"))
    run_parser.add_argument("--no-build", action="store_true")
    run_parser.add_argument("--mode", choices=("accurate", "fast"), default="fast")
    audio_group = run_parser.add_mutually_exclusive_group()
    audio_group.add_argument("--audio", action="store_true")
    audio_group.add_argument("--no-audio", action="store_true")

    test_parser = subparsers.add_parser(
        "test", help="run host, target-compiler, and emulator verification"
    )
    test_parser.add_argument(
        "--full", action="store_true",
        help=(
            "also run every firmware integration, maintained sample build, "
            "and complete-sample runtime check"
        ),
    )

    args = parser.parse_args()
    if args.command == "doctor":
        return doctor(as_json=args.json)
    if args.command == "build":
        project = load_project(args.target)
        build_project(project, install_nand=args.nand)
        return 0
    if args.command == "run":
        project = load_project(args.target)
        mba = project.mba if args.no_build else build_project(project)
        if not mba.is_file():
            fail(f"MBA does not exist; run the build command first: {mba}")
        run_emulator(project, mba, mode=args.mode, audio=args.audio and not args.no_audio)
        return 0
    if args.command == "test":
        make = shutil.which("make")
        if make:
            if args.full:
                run([make, "release-check"])
            else:
                # The ordinary gate is deliberately broad enough to catch the
                # mistakes that matter to a new title: portable SDK behavior,
                # packaging scripts, target compilation, and emulator device
                # regressions.  The full gate additionally runs every slower
                # firmware/application integration scenario, sample build, and
                # complete-sample runtime check.
                for target in QUICK_TEST_TARGETS:
                    run([make, target])
        else:
            if platform.system() != "Windows":
                fail("Make is required for the test suite on macOS and Linux")
            if args.full:
                fail(
                    "test --full requires Make, a GCC-compatible host C compiler, "
                    "CMake, and SDL2; install the documented Windows/MSYS2 "
                    "test prerequisites so no release checks are skipped"
                )
            print(
                "NOTE Make is unavailable: running the bounded native-Windows "
                "baseline (Python/USB, target objects, project build, and the "
                "automatic-controls firmware/emulator integration). Host-C "
                "tests and Emulator2 CTests require the documented Make setup."
            )
            for command in WINDOWS_NO_MAKE_TEST_SCRIPTS:
                run(python_command(*command))
            build_project(load_project())
        return 0
    fail(f"unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
