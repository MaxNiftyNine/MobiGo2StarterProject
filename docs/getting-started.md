# Getting started

## Requirements

macOS needs Python 3 and Wine. Windows needs Python 3; the target tools run
natively. The repository supplies the Generalplus u'nSP IDE 4.1.1 toolchain,
linker bodies, Emulator2, and split development NAND image.

For a macOS emulator rebuild, install CMake, pkg-config, and SDL2. Host SDK
tests additionally need Make and a C99 compiler.

## Build and run

The launchers compile `app/main.c`, link all SDK sources, generate the standard
system UI, package `build/MobiGo2Starter.MBA`, create
`build/nand.edited.bin`, and start Emulator2.

```sh
./scripts/build_and_run.command --no-audio
```

```powershell
.\scripts\build_and_run.ps1 -NoAudio
```

The source `vendor/firmware/nand.us-stitched.bin` is verified and remains unchanged.
If it has not been assembled yet, the build reconstructs it from the tracked
parts.

## Build only

```sh
python3 tools/build/build_sdk_app.py app/main.c \
  --output-dir build \
  --slot SY \
  --name MobiGo2Starter
```

Useful options:

- `--slot G1` selects the G1 load and entry profile.
- `--extra-source path/to/generated.c` links another C or u'nSP assembly file
  and adds its directory to the include search path. Repeat it as needed.
- `--with-clean-font` generates and links the ASCII font.
- `--without-system-ui` omits the standard system-control bundle.
- `--menu-tile tile.bin --palette palette.bin` supplies custom launcher art.
- `--install-nand --nand-output build/nand.edited.bin` creates an emulator NAND.

## Complete examples

The repository includes three complete G1 projects in addition to the focused
API probes and SY hardware suite:

```sh
make samples
```

That builds Color Cycle, the monochrome movie player, and MobiGo Celeste. See
the [sample projects](samples.md) page for controls, media generation, and
individual build commands.

## Emulator controls

Arrow keys map to both the D-pad and matching motion tilt, Control to the
primary button, Escape to Exit, and
F12 closes the emulator. The complete physical matrix and scripted key names
are documented in `docs/reference/INPUT_MATRIX.md`.

## Real hardware

After building, install the default SY MBA with:

```sh
./scripts/usb/install_mba.command --system build/MobiGo2Starter.MBA
```

Windows users can run `scripts\usb\install_mba.bat`. Read the USB tool guide first,
and keep recovery dumps: a bad SY replacement can interrupt normal boot.
