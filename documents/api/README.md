# MobiGo 2 C/C++ API

This is an experimental, freestanding, source-derived hardware abstraction for the MobiGo 2
behavior implemented by `mobigo2_programmer_kit/emu`. It is not an official
VTech or Generalplus SDK.

It predates the final retail G1 callback discoveries and is not a
hardware-confirmed complete ABI. Use it as a register/abstraction reference;
use `examples/color_cycle` as the starting point for a physical-device MBA.

## Files

- `include/mobigo2.h`: stable scalar C ABI, also safe to include from C++.
- `include/mobigo2.hpp`: optional idiomatic C++ wrappers.
- `src/mobigo2.c`: implementation.
- `src/unsp_bridge.asm`: three-instruction DS/far-memory bridge required by the
  current vbcc unSP backend.

## Coverage

The API exposes:

- 22-bit word memory and direct RGB565 framebuffer drawing.
- Video timing, framebuffer input/output, frame synchronization and PPU compose.
- Palette banks, four PPU layers, row scroll, sprites and local video DMA.
- GPIO ports, six-by-nine key matrix, manual ADC, battery and touch contact.
- Four-channel system DMA and interrupt-controller status/acknowledgement.
- Four timers, three timebases, RTC scheduler and clock registers.
- Watchdog, reset cause and sleep request.
- SPI NOR reads/ID/status and NAND read/program/erase primitives.
- DAC FIFO status, cache completion, USB status and stored SD2 registers.

## Compiler constraints

PulkoMandy's vbcc unSP backend is currently a C compiler with a 16-bit pointer
model. It accepts some struct and C++-looking syntax but does not implement a
correct multiword-struct ABI. For that reason the supported target ABI uses
explicit low/high address arguments and ordinary 16-bit scalar parameters.

The C++ wrapper is ready for a future unSP C++ frontend and can also be used for
host-side code completion. The supplied target build compiles `main.cpp` as the
C-compatible freestanding subset because no working unSP C++ frontend is known.

## Emulator limitations reflected by the API

- Audio support in this older API does not represent the later retail output
  gate discovery. See `docs/CONFIRMED_HARDWARE_RULES.md`.
- USB and SD2 transfers are not implemented; only modeled/stored state is exposed.
- Row zoom, transforms, SPU playback and several auxiliary peripherals are stored
  but not rendered or executed.
- FIQ delivery is incomplete. Prefer IRQ routing.
- NAND program and erase calls modify the emulator NAND image; the test project
  intentionally does not call them.
- Touch contact and raw ADC are supported. Exact coordinate scaling should be
  calibrated by applications for real hardware.

See the separate `Mobigo2APITestCpp` project for a buildable example.
