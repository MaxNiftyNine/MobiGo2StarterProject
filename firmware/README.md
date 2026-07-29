# Included MobiGo 2 firmware set

These files make the emulator and G1/SY packaging workflows usable
without locating separate dumps:

| File | Size | SHA-256 |
|---|---:|---|
| `internalrom.bin` | 131,072 | `883e2d2111bf978af1b98fcf34f577c46739da8778c1cec592be79a6f6b4d5d5` |
| `spi.bin` | 2,097,152 | `13c8b101afe2e04cccdc0e42d3134d2d06657057d8d6f6a84954dce4d6c230d3` |
| `nand.us-stitched.bin.part00` + `nand.us-stitched.bin.part01` | 138,412,032 combined | `66e686225f709e07ca0d76b78b82374cb6fd27296c7a3d8b98c765da66442e7a` |
The build-and-run scripts create `build/MobiGo2Starter.MBA` entirely from the
compiled payload and deterministic slot-profile metadata. No application
container is extracted from the NAND. In the edited image, the generated MBA
is installed at the existing SY slot filename.

## Reassemble the NAND before use

The US stitched NAND is stored as numbered parts because the complete 132 MiB
image exceeds GitHub's per-file limit. Before using the emulator or NAND tools,
reassemble it from the repository root:

```sh
python3 tools/assemble_nand.py
```

This creates `firmware/nand.us-stitched.bin` and verifies both its exact size
and SHA-256. The build-and-run scripts perform this same step automatically.
The assembled file is ignored by Git and must not be committed.

## Redistribution notice

These are VTech/device-derived binaries, not original homebrew source code.
Their inclusion does not grant a license to redistribute or modify them.
Anyone publishing this pack should independently confirm that they have the
necessary rights or distribute a firmware-free edition instead.

Always retain an untouched backup before modifying or flashing device storage.
