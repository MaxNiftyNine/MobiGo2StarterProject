# Celeste Classic for MobiGo 2

This is an optimized MobiGo 2 port of Celeste Classic's original PICO-8 game
logic. It is included as an advanced sample: a packed 128x128 4-bpp logical
framebuffer is scaled to the centered 240x240 display with an assembly 15:8
nearest-neighbor scaler and DMA staging rows.

## Controls

- D-pad, `W`/`A`/`S`/`D`, or emulator arrow keys: move
- Primary, `E`, or Enter: jump/start
- Help, Brightness, `X`, F1/F6, or Space: dash

## Build

On Windows, run the following from this directory:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\build.ps1
```

The script prefers the toolkit's bundled Generalplus u'nSP IDE, then honors
`UNSP_IDE`, and finally tries the standard IDE installation path. It writes
the payload to `build\app.bin`. Package that payload with the top-level MBA
tools and a verified G1 donor to launch it on the emulator or hardware.

`src/assets.h` is the checked-in, compiler-ready asset header. To regenerate
it after editing `reference/gfx.bmp`, `reference/font.bmp`, or
`reference/tilemap.h`, install Pillow and run:

```sh
python3 tools/generate_assets.py
```

The sample is a source example only; firmware, emulator binaries, and generated
MBA/NAND files are intentionally not duplicated here. Celeste Classic and its
artwork remain subject to their respective owners' rights.

## Layout

- `src/` contains the game logic, MobiGo frontend, generated assets, and scaler.
- `reference/` contains the inputs used to generate `src/assets.h`.
- `CelestePico8G1.bdy` reserves the game's internal-RAM scratch buffers.
- `tools/build.ps1` compiles the payload; `tools/srec_to_bin.py` converts it.
