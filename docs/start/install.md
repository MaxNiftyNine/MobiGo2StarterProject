# Install on Windows, macOS, or Linux

The unified CLI reports exact missing prerequisites:

```sh
python3 tools/mobigo.py doctor
```

Run commands from the repository root. Paths elsewhere in the manual assume
that working directory.

## Shared requirements

- Python 3.10 or newer is required.
- Enough free space for a 132 MiB assembled NAND plus disposable copies.
- The tracked Generalplus target tools, linker profiles, and split firmware
  inputs must be present under `vendor/`.
- A C99 compiler and Make are needed for host SDK tests.
- CMake, SDL2 development files, and `pkg-config` are needed when building
  Emulator2 from source.

Clone with submodules, or initialize them in an existing checkout:

```sh
git submodule update --init --recursive
```

The Generalplus target executables run natively on Windows and through Wine on
macOS and Linux.

=== "Windows"

    1. Install 64-bit Python 3 and enable the launcher (`py`).
    2. Install MSYS2, then install the MINGW64 packages for GCC, CMake, Ninja,
       and SDL2:

       ```text
       mingw-w64-x86_64-toolchain mingw-w64-x86_64-cmake
       mingw-w64-x86_64-ninja mingw-w64-x86_64-SDL2
       ```

       The unified CLI builds the emulator submodule into
       `build/emulator-host/` when it is first needed. As an alternative,
       download a packaged emulator release and set `MOBIGO_EMULATOR` to its
       executable.
    3. For USB device tools, install:

       ```powershell
       py -3 -m pip install -r .\tools\usb\requirements-windows.txt
       ```

    Diagnose and run:

    ```powershell
    py -3 tools\mobigo.py doctor
    py -3 tools\mobigo.py run
    ```

    The normal test command has a bounded no-Make baseline. For the complete
    host-C and Emulator2 CTest suite, use an MSYS2 environment with Make, a
    GCC-compatible C/C++ compiler, CMake, `pkg-config`, and SDL2 development
    packages. `test --full` fails clearly when that complete setup is absent.

=== "macOS"

    Install Python, CMake, SDL2, and `pkg-config`. With Homebrew:

    ```sh
    brew install python cmake sdl2 pkg-config
    ```

    Install a Wine distribution that can run 32-bit Windows tools, then ensure
    both `wine` and `winepath` are on `PATH`. Homebrew Wine packages are casks,
    so follow the current cask instructions for the distribution you select.

    Apple Silicon Wine compatibility depends on the installed Wine distribution.
    `doctor` reports whether both `wine` and `winepath` are usable.

    ```sh
    python3 tools/mobigo.py doctor
    python3 tools/mobigo.py run
    ```

=== "Linux"

    Install Python, Wine with 32-bit executable support, CMake, SDL2 development
    files, `pkg-config`, Make, and a C/C++ compiler. Package names vary. On a
    Debian-family system, enable the i386 architecture if required by its Wine
    packages, then install the equivalents of:

    ```sh
    sudo apt install python3 wine wine32:i386 cmake libsdl2-dev pkg-config build-essential
    ```

    Confirm that `winepath` is installed along with Wine, then run:

    ```sh
    python3 tools/mobigo.py doctor
    python3 tools/mobigo.py run
    ```

## Firmware assembly

The NAND is tracked in split parts because the complete raw image exceeds
GitHub's single-file size limit. The normal CLI assembles and verifies it when
needed. To do that explicitly:

```sh
python3 tools/nand/assemble_nand.py
```

The result is `vendor/firmware/nand.us-stitched.bin`. It is ignored by Git. Run
uses the emulator's in-memory overlay. It never creates an edited NAND as a
compatibility fallback. `build --nand` remains an explicit persistent-filesystem
validation tool; no workflow modifies the source image.

## Documentation environment

```sh
python3 -m pip install -r docs/requirements.txt
mkdocs serve
```

## Optional tools

- Emscripten is required only for the browser emulator build.
- Pillow and media conversion packages are required only by the generators that
  name them.
- Ghidra, Gradle, and `ghidra-unSP` are required only for reverse engineering.
- Physical USB installation has additional privilege and recovery requirements;
  see [NAND and USB tools](../tools/nand-usb.md).

## Diagnose before guessing

If a command fails, rerun `doctor` and keep its full output. Do not work around
a missing target tool by switching to an older G1-specific build wrapper.
