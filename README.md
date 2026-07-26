# THIS IS AI SLOP LIKE EVERYTHING I DO, but it works
im sorry, not sorry.
anyways so that means that this project is not meant for humans, its meant for you to say something crazy to codex like "make me minecraft for mobigo" and it just does it without any work you lazy shit


For testing on a real mobigo2 see https://github.com/MaxNiftyNine/VTech-MobiGo2-Reverse-Engineering-Dump
(currently homebrew runs by replacing hampster highway so if you want it back Learning Lodge should automatically repair it)

# MobiGo 2 starter project

This folder is a self-contained starting point for a retail-menu-loadable
MobiGo 2 application. The default program is the hardware-confirmed color-cycle
demo. One command builds it with the Generalplus u'nSP compiler, packages the
payload inside a verified retail G1 donor MBA, creates a new edited NAND
without changing the source NAND, boots Emulator2, selects **Hamster Highway**
and **Easy** automatically, and opens the emulator window after the two menu
presses.

## Start on macOS

Make sure the Windows build computer is reachable over SSH, then double-click
`build_and_run.command` or run:

```sh
./build_and_run.command --no-audio
```

The default SSH destination is `max@DESKTOP-BTTG0A6.local`. Override it with:

```sh
MOBIGO_BUILD_HOST=user@windows-pc.local ./build_and_run.command
```

SSH keys are recommended. If necessary, install `sshpass` and provide
`MOBIGO_SSH_PASSWORD` in the environment; the script never stores a password.
The Mac handles MBA packaging, verified NAND replacement, and emulation. SSH is
used only for the proprietary Generalplus compilation step.
The large NAND dump is stored as GitHub-safe parts; the script reassembles and
verifies it automatically before use. To use emulator tools directly, first run
`python3 tools/assemble_nand.py`.
Before launching, the script asks whether to emulate host audio. Choose `y` for
audio playback, or press Enter to keep it off for faster execution.
Pass `--audio` or `--no-audio` to skip that question.

An Apple Silicon emulator and its SDL2 runtime are included. On a different Mac
architecture, `tools/build_emulator_macos.sh` rebuilds from the included source
when CMake, pkg-config, and SDL2 are installed.

## Start on Windows

Right-click `build_and_run.ps1` and choose **Run with PowerShell**, or run:

```powershell
powershell -ExecutionPolicy Bypass -File .\build_and_run.ps1 -NoAudio
```

You can also double-click `build_and_run.bat`.

The script uses the bundled compiler first, then `UNSP_IDE`, then the standard
Generalplus u'nSP IDE 4.1.1 installation path. Python 3 is required.
It automatically reassembles the split NAND before use. For direct emulator or
NAND-tool use, run `python tools\assemble_nand.py` first.
Before launching, it asks whether to emulate host audio; press Enter to leave it
off for faster execution. Pass `-Audio` or `-NoAudio` to skip that question.

## Edit the program

Start with:

```text
src/main.c
```

The starter deliberately avoids initialized global/static data because the G1
entry jumps directly into `main()` without normal C runtime initialization.
Keep inherited IRQ/FIQ enabled, service the watchdog, use the launcher-selected
FBI/FBO buffers, and do not return from a resident application. Read
`documents/documentation/CONFIRMED_HARDWARE_RULES.md` before replacing the
demo loop.

Build products are written only under `build/`:

```text
app.bin
MobiGo2Starter.MBA
nand.edited.bin
```

The original donor and NAND under `firmware/` are read-only inputs to the
scripts and are verified after replacement.

## Included material

- `documents/documentation`: programmer guide, MBA development guide,
  confirmed hardware rules, u'nSP 2.0 manual, GPL16250VA datasheet, and the
  corrected full input matrix.
- `documents/samples`: color cycle, MobiPong, and Bad Apple sample projects.
- `documents/api`: the experimental MobiGo 2 C/C++ abstraction layer.
- `firmware`: internal ROM, SPI image, US stitched NAND, and verified G1 donor.
- `emulator`: Emulator2 source, tests, macOS binary, and Windows binary.
- `compiler/windows`: the Generalplus compiler files required by the build.

## Emulator controls

Arrow keys are the large D-pad, Control is Primary, Escape is Exit, and F12
closes the emulator. See
`documents/documentation/INPUT_MATRIX.md` for every physical matrix cell,
host binding, and scripted key name.

## Safety

The automation never edits `firmware/nand.us-stitched.bin`. It creates
`build/nand.edited.bin`. Emulator success does not guarantee hardware success;
keep verified recovery dumps and do not overwrite the only copy of a real
device's NAND or SPI.

## Validation performed on this template

- macOS SSH compilation, MBA packaging, NAND replacement, and read-back: pass;
- Windows-local compilation using the bundled compiler: pass;
- Windows x64 emulator startup with the included DLLs: pass;
- automated Hamster Highway/Easy launch to the resident color demo: pass;
- emulator audio, watchdog, and hardware-accuracy unit tests: 3/3 pass;
- all documented `--key-event` matrix names: parse and execute successfully.

Generated files were removed after testing so the checked-in `build/` directory
is clean.
