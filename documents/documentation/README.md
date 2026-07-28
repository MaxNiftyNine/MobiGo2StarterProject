# MobiGo 2 Homebrew Developer Pack

This is a community reverse-engineering pack for writing Generalplus unSP C
programs and testing them in the included emulator before trying them on
hardware. The starter build-and-run commands target the boot-time SY slot;
older samples and confirmed hardware research also cover G1.

Start with [QUICKSTART.md](QUICKSTART.md), then read
[docs/CONFIRMED_HARDWARE_RULES.md](docs/CONFIRMED_HARDWARE_RULES.md). The
long-form July 14 reverse-engineering snapshot is
[docs/mobigo2_mba_development_guide.md](docs/mobigo2_mba_development_guide.md);
where its older status statements conflict, the status matrix and confirmed
hardware rules take precedence.

For installing an MBA on real hardware, toggling developer mode, or checking
device storage on macOS and Windows, see the
[MobiGo 2 USB tools README](../../tools/mobigo_usb/README.md).

## What is included

- A real-hardware-confirmed color-cycle C example.
- Experimental Bad Apple video/audio source without copyrighted media.
- An emulator-verified Pong experiment, clearly labeled as such.
- A donor-preserving G1 MBA packer and MBA inspector.
- SY support in the donor-preserving packer and MOBIGOFS replacement wrapper.
- The MobiGo 2 emulator source, including the hardware behaviors discovered
  while getting homebrew to run on a physical unit.
- An experimental C/C++ hardware-abstraction layer.
- Current and archived research documentation.
- A ready-to-run firmware set in `firmware/`, including the verified G1 donor.

## What is deliberately not included

- Patched MBA outputs containing bytes from a retail donor.
- Generalplus IDE/compiler binaries or confidential vendor datasheets.
- Bad Apple video, audio, or MIDI assets.
- Credentials or machine-specific personal paths.

The included firmware and G1 donor are vendor/device data and are not covered by
the homebrew source material's licensing. Confirm that you have permission to
redistribute them before publicly mirroring the ZIP. See
[firmware/README.md](firmware/README.md) and
[third_party/README.md](third_party/README.md).

## Known-good target

The default starter automation targets the included SY layout:

- MBA entry: `0x0DFC1D`
- File offset corresponding to the entry: `0x2F83A`
- Next protected callback: `0x0F3E60`
- Runtime-to-file word-address bias: `0x0C8000`
- Maximum replacement window: 164,998 bytes

The real-hardware-confirmed sample workflow targets a retail
`135804G1.MBA`-layout donor:

- MBA entry: `0x0E1A55`
- File offset corresponding to the entry: `0x334AA`
- Next protected callback: `0x0F3E5C`
- Runtime-to-file word-address bias: `0x0C8000`
- Maximum replacement window: 149,518 bytes
- Generalplus IDE body: `GPL16250VA_CS0SRAM`

Those values are layout-specific. Do not assume they apply to another MBA.

## Important status

The color-cycle demo and silent Bad Apple video path were observed working on
real MobiGo 2 hardware. Bad Apple audio revision V6 implements the retail output
gate sequence and passes emulator tests, but has not yet been confirmed audible
on physical hardware. See [docs/STATUS_MATRIX.md](docs/STATUS_MATRIX.md).

## Public sharing and licensing

This pack combines original research/code with files whose upstream license was
not always declared. No blanket license is asserted. Read
[SHARING_NOTES.md](SHARING_NOTES.md) before mirroring or redistributing it.

Run `python3 tools/verify_pack.py` before publishing a copy.
