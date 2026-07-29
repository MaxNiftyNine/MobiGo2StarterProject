# MobiGo 2 Homebrew Developer Pack

This is a community reverse-engineering pack for writing Generalplus unSP C
programs and testing them in the included emulator before trying them on
hardware. The starter build-and-run commands target the boot-time SY slot;
older samples and confirmed hardware research also cover G1.

Start with [QUICKSTART.md](QUICKSTART.md), then read
[CONFIRMED_HARDWARE_RULES.md](CONFIRMED_HARDWARE_RULES.md). The active
from-scratch workflow is documented in
[mobigo2_mba_development_guide.md](mobigo2_mba_development_guide.md).

The cross-sample executable-container specification and Ghidra loader guide
are in [mobigo_mba_format.md](mobigo_mba_format.md).

For installing an MBA on real hardware, toggling developer mode, or checking
device storage on macOS and Windows, see the
[MobiGo 2 USB tools README](../../tools/mobigo_usb/README.md).

## What is included

- A real-hardware-confirmed color-cycle C example.
- Experimental Bad Apple video/audio source without copyrighted media.
- An emulator-verified Pong experiment, clearly labeled as such.
- A deterministic G1/SY MBA generator and Ghidra loader.
- A filesystem-aware G1/SY MOBIGOFS installation wrapper.
- The MobiGo 2 emulator source, including the hardware behaviors discovered
  while getting homebrew to run on a physical unit.
- An experimental C/C++ hardware-abstraction layer.
- Current and archived research documentation.
- A ready-to-run emulator firmware set in `firmware/`.

## What is deliberately not included

- Generated build outputs.
- Generalplus IDE/compiler binaries or confidential vendor datasheets.
- Bad Apple video, audio, or MIDI assets.
- Credentials or machine-specific personal paths.

The included firmware is vendor/device data and is not covered by the
homebrew source material's licensing. Confirm redistribution rights before
publicly mirroring it. See [firmware/README.md](../../firmware/README.md) and
[THIRD_PARTY.md](../../THIRD_PARTY.md).

## Known-good target

The default starter automation targets the included SY layout:

- MBA entry: `0x0DFC1D`
- File offset corresponding to the entry: `0x2F83A`
- Next protected callback: `0x0F3E60`
- Runtime-to-file word-address bias: `0x0C8000`
- Maximum generated payload: 164,998 bytes

The generated G1 profile uses:

- MBA entry: `0x0E1A55`
- File offset corresponding to the entry: `0x334AA`
- Next protected callback: `0x0F3E5C`
- Runtime-to-file word-address bias: `0x0C8000`
- Maximum generated payload: 149,518 bytes
- Generalplus IDE body: `GPL16250VA_CS0SRAM`

Those values are layout-specific. Do not assume they apply to another MBA.

## Important status

The color-cycle demo and silent Bad Apple video path were observed working on
real MobiGo 2 hardware. Bad Apple audio revision V6 implements the retail output
gate sequence and passes emulator tests, but has not yet been confirmed audible
on physical hardware. See [STATUS_MATRIX.md](STATUS_MATRIX.md).

## Public sharing and licensing

This pack combines original research/code with files whose upstream license was
not always declared. No blanket license is asserted. Read
[SHARING_NOTES.md](SHARING_NOTES.md) before mirroring or redistributing it.

Run `python3 ../../tools/test_build_mba.py` after packaging changes.
