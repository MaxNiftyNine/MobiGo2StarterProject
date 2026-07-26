# Quick start

## 1. Install the verified compiler

On Windows, install Generalplus unSP IDE 4.1.1. If it is not at the default
location, set `UNSP_IDE` to its installation directory before running a build:

```powershell
$env:UNSP_IDE = 'D:\Tools\Generalplus\unSPIDE_4.1.1'
```

The open vbcc/vasm/vlink route in `tools/build_experimental_open_toolchain.sh`
is useful for research, but it did not produce the final hardware-confirmed
examples in this pack.

## 2. Build the smallest confirmed example

Copy `examples/color_cycle` to the Windows computer and run:

```powershell
powershell -ExecutionPolicy Bypass -File tools\build.ps1
```

This produces `build\color_cycle.bin`. The program is linked at word address
`0x0E1A55` for the verified G1 callback layout.

## 3. Inspect the included retail G1 donor

The development pack includes the verified donor at `firmware/G1-stock.MBA`.
Inspect it before use:

```sh
python3 tools/inspect_mba.py firmware/G1-stock.MBA
```

For the supported layout, the entry must be `0xe1a55` and its file offset must
be `0x334aa`.

## 4. Package the payload

```sh
python3 tools/pack_g1_mba.py \
  --donor firmware/G1-stock.MBA \
  --payload /path/to/color_cycle.bin \
  --output /path/to/COLOR_CYCLE_G1.MBA
```

The packer preserves the header, loader tables, protected callback area, and
file length. It refuses unexpected donors and oversized payloads.

## 5. Test in the emulator without changing NAND

The NAND dump is checked in as numbered parts to stay below GitHub's file-size
limit. Reassemble and verify it before using the emulator:

```sh
python3 tools/assemble_nand.py
```

Build the included emulator:

```sh
cmake -S emulator -B emulator/build
cmake --build emulator/build
```

Run with the included firmware images:

```sh
emulator/build/mobigo2_emu \
  --rom firmware/internalrom.bin \
  --spi firmware/spi.bin \
  --nand firmware/nand.us-stitched.bin \
  --mba /path/to/COLOR_CYCLE_G1.MBA
```

The `--mba` option substitutes an MBA in memory; it does not modify the source
NAND. For a G1 application, create a separate edited NAND instead:

```sh
python3 tools/replace_g1_in_nand.py \
  firmware/nand.us-stitched.bin \
  /path/to/COLOR_CYCLE_G1.MBA \
  /path/to/nand.edited.bin
```

Boot the edited image, choose **Hamster Highway**, then **Easy**.

## 6. Hardware

Work only from verified backups and retain an unmodified recovery image. The
pack does not include a universal flasher. Install the MBA through a filesystem
method appropriate to your own device, preserving both MOBIGOFS snapshots when
required. Never overwrite your only NAND/SPI backup.

Emulator success is necessary but not sufficient. Before hardware testing,
check every rule in `docs/CONFIRMED_HARDWARE_RULES.md`.
