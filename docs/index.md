# MobiGo 2 Homebrew SDK

This project turns `app/main.c` into a complete MobiGo 2 MBA and runs it in an
emulator. The starter is linked against a clean-room SDK reconstructed from the
common runtime behavior shared by official games.

It includes resident lifecycle, input, touch, system controls, storage,
graphics resources, UI animation, PCM/ADPCM effects, sequenced music, a
from-scratch MBA packager, NAND and USB tools, and a Ghidra MBA/GAM loader.

No donor game is used by the builder. The resulting MBA format has been
reported working on physical MobiGo 2 hardware.

## First build

=== "macOS"

    ```sh
    ./scripts/build_and_run.command --no-audio
    ```

=== "Windows"

    ```powershell
    .\build_and_run.ps1 -NoAudio
    ```

Then edit `app/main.c` and repeat. Read [Getting started](getting-started.md)
before changing memory allocation or the application lifecycle.

## What is verified

- Clean-room C components have host regression tests.
- SDK sources compile with the bundled Generalplus compiler.
- Complete SY and G1 MBAs are generated from source and format metadata.
- The resident lifecycle, system UI, storage, font, animation, and audio paths
  have end-to-end emulator checks.
- The Ghidra loader maps compacted MBA pages, GAM variants, firmware services,
  and known MMIO registers.

See [Project status](status.md) for the evidence boundary and remaining work.
