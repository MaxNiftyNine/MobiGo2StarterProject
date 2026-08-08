#!/usr/bin/env python3
"""Build the emulator submodule with a native Windows CMake/SDL2 toolchain."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess


ROOT = Path(__file__).resolve().parents[2]
BUILD = ROOT / "build" / "emulator-host"


def find(name: str) -> str:
    for directory in (Path(r"C:\msys64\mingw64\bin"), Path(r"C:\mingw64\bin")):
        candidate = directory / (name + ".exe")
        if candidate.is_file():
            return str(candidate)
    found = shutil.which(name)
    if found:
        return found
    raise SystemExit(
        f"{name} was not found. Install CMake, Ninja, GCC, and SDL2, "
        "or install the MINGW64 packages documented in docs/start/install.md."
    )


def main() -> int:
    gxx = find("g++")
    runtime_directory = Path(gxx).parent

    def companion(name: str) -> str:
        candidate = runtime_directory / f"{name}.exe"
        return str(candidate) if candidate.is_file() else find(name)

    cmake = companion("cmake")
    ctest = companion("ctest")
    ninja = companion("ninja")
    environment = os.environ.copy()
    tool_directories = dict.fromkeys(
        str(Path(tool).parent) for tool in (cmake, ctest, ninja, gxx)
    )
    environment["PATH"] = os.pathsep.join(
        [*tool_directories, environment.get("PATH", "")]
    )
    subprocess.run(
        [
            cmake, "-S", str(ROOT / "emulator"), "-B", str(BUILD),
            "-G", "Ninja", "-DCMAKE_BUILD_TYPE=Release", "-DBUILD_TESTING=ON",
            f"-DCMAKE_MAKE_PROGRAM={ninja}",
            f"-DCMAKE_CXX_COMPILER={gxx}",
            f"-DCMAKE_PREFIX_PATH={runtime_directory.parent}",
        ],
        check=True, env=environment,
    )
    subprocess.run([cmake, "--build", str(BUILD), "--parallel"], check=True, env=environment)
    subprocess.run([ctest, "--test-dir", str(BUILD), "--output-on-failure"], check=True, env=environment)
    executable = BUILD / "mobigo2_emu.exe"
    if not executable.is_file():
        raise SystemExit(f"Windows emulator build did not produce {executable}")
    for name in (
        "SDL2.dll",
        "libgcc_s_seh-1.dll",
        "libstdc++-6.dll",
        "libwinpthread-1.dll",
    ):
        source = runtime_directory / name
        if not source.is_file():
            raise SystemExit(f"required Windows emulator runtime is missing: {source}")
        shutil.copy2(source, BUILD / name)
    print(executable)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
