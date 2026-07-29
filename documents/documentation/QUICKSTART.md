# Quick start

The project builds a complete MobiGo 2 SY application container from source.
It does not read or patch an existing MBA.

## macOS

Install Python 3 and Wine, then run:

```sh
./build_and_run.command --no-audio
```

For a build without launching the emulator:

```sh
MOBIGO_NO_LAUNCH=1 ./build_and_run.command --no-audio
```

The workflow:

1. compiles `src/main.c` at word address `0x0dfc1d`;
2. creates `build/app.bin`;
3. synthesizes the complete header, launcher resources, body, and CRC;
4. writes `build/MobiGo2Starter.MBA`;
5. installs it into a separate `build/nand.edited.bin`; and
6. boots that edited image.

The original NAND is never modified.

## Windows

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\build_and_run.ps1 -NoAudio
```

Use `-NoLaunch` to stop after the build and NAND read-back verification.

## Package an existing payload manually

For the boot-time SY slot:

```sh
python3 tools/build_mba.py \
  --slot SY \
  --payload build/app.bin \
  --output build/MobiGo2Starter.MBA
```

For a payload linked at the G1 entry:

```sh
python3 tools/build_mba.py \
  --slot G1 \
  --payload /path/to/g1-linked.bin \
  --output build/HomebrewG1.MBA
```

The payload must be linked for the selected entry. Changing only `--slot`
does not relocate machine code.

Optional `--palette` and `--menu-tile` arguments accept a raw 32-byte RGB555
palette and a raw `0xd00`-byte 64x104 indexed 4-bpp visible tile. The
profile-specific launcher footer is always generated separately.

## Install into an emulator NAND

```sh
python3 tools/assemble_nand.py
python3 tools/install_mba_in_nand.py \
  firmware/nand.us-stitched.bin \
  build/MobiGo2Starter.MBA \
  build/nand.edited.bin \
  --slot SY
```

The installer updates every matching filesystem snapshot and reopens the
result to verify the complete MBA byte-for-byte.

## Install on hardware

Keep verified recovery images. Install the default SY-linked build with:

```sh
./mobigo_install_mba.command --system build/MobiGo2Starter.MBA
```

Windows uses `mobigo_install_mba.bat` with the same arguments. See
[`tools/mobigo_usb/README.md`](../../tools/mobigo_usb/README.md) for device
setup and recovery warnings.

The from-scratch SY image has passed the complete normal-boot path in
Emulator2. Physical-device confirmation of this newly generated container is
still required.
