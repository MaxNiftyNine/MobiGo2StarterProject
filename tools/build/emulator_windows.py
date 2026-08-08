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
    found = shutil.which(name)
    if found:
        return found
    candidate = Path(r"C:\msys64\mingw64\bin") / (name + ".exe")
    if candidate.is_file():
        return str(candidate)
    raise SystemExit(
        f"{name} was not found. Install CMake, Ninja, GCC, and SDL2, "
        "or install the MINGW64 packages documented in docs/start/install.md."
    )


def main() -> int:
    cmake = find("cmake")
    ctest = find("ctest")
    ninja = find("ninja")
    gxx = find("g++")
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
            "-DCMAKE_PREFIX_PATH=C:/msys64/mingw64",
        ],
        check=True, env=environment,
    )
    subprocess.run([cmake, "--build", str(BUILD), "--parallel"], check=True, env=environment)
    subprocess.run([ctest, "--test-dir", str(BUILD), "--output-on-failure"], check=True, env=environment)
    executable = BUILD / "mobigo2_emu.exe"
    if not executable.is_file():
        raise SystemExit(f"Windows emulator build did not produce {executable}")
    runtime_directory = Path(gxx).parent
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
