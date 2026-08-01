# MobiGo 2 GPL16250 / unSP Emulator

This is a standalone correctness-first emulator for the VTech MobiGo 2 firmware
images in this workspace. It currently implements a unSP interpreter, internal ROM
reset-vector boot, a SPI NOR transaction model, a GPL16250/GPAC800-style memory
map, NAND raw-page access, and an SDL2 graphics window. The stock dumps now
boot far enough to display the firmware-generated VTech logo screen. The
GPL16250 direct DAC and 32-channel SPU are also emulated and sent to SDL2 as
stereo audio.

The intended retail boot sequence is:

```text
VTech logo -> MobiGo animation -> LD loading screen -> game select screen
```

Do not replace missing stages with hardcoded screens. If the emulator does not
advance to the next stage, treat that as a hardware-emulation gap in CPU, MMIO,
DMA, NAND/SPI, interrupts, timing, input, or rendering.

Build:

```sh
cmake -S . -B build
cmake --build build
```

For the fastest macOS/Clang binary, train a profile-guided build against the
retail boot path:

```sh
./pgo_build.sh
../build/emulator-pgo/mobigo2_emu --no-window --steps 100000000 \
  --rom ../vendor/firmware/internalrom.bin \
  --spi ../vendor/firmware/spi.bin \
  --nand ../vendor/firmware/nand.us-stitched.bin
```

Set `TRAIN_STEPS=...` to change the PGO training run length.

Run:

```sh
./build/mobigo2_emu \
  --rom ../vendor/firmware/internalrom.bin \
  --spi ../vendor/firmware/spi.bin \
  --nand ../vendor/firmware/nand.us-stitched.bin
```

The prebuilt 64-bit Windows executable is in `bin/windows/` with the matching
SDL2 and MinGW/GCC runtime DLLs and their license notices.

Host audio is off by default. Pass `--audio` for playback in a windowed run.
The implementation supports direct DAC FIFO playback and SPU PCM8, PCM16, IMA
ADPCM, and ADPCM36, including pitch, pan, volume/envelopes, looping, FIFO
status, and IRQ/FIQ refill signaling. Silent and headless runs still advance
audio hardware state without opening a host device or throttling execution.

Windowed desktop runs are capped to the MobiGo 2's emulated hardware time by
default. The cap integrates CPU cycles using the live system-clock source, PLL
multiplier, and divider rather than assuming a fixed instruction rate. Use
`--no-cap` to allow a windowed run to execute as quickly as the host permits.
`--no-window` runs are always uncapped. Host audio, VSync, or the desktop
compositor can still make a run slower; the cap does not speed up a slow host.

`--mba PATH` replaces the `MM.MBA` copy in both recoverable MOBIGOFS snapshots,
including `/DEFAULT/MM.MBA`
and the active language directory. If the MBA exceeds the original allocation,
the overlay maps additional erased NAND blocks in memory. The source NAND and
its OOB data on disk are never changed. When `--mba` is combined with `--usb`,
guest NAND writes are also discarded at exit so the transient overlay cannot be
saved accidentally.

The transient MBA handoff also models the watchdog state inherited from the
retail loader. The watchdog is armed when execution reaches the MBA header's
entry address and requests a full system reset after two seconds unless the MBA
services or disables it through `P_Watchdog_Clear` (`0x780b`) and
`P_Watchdog_Ctrl` (`0x780a`). This exposes startup code that can appear to work
in a permissive emulator but reboot a real MobiGo 2.

MBA headers loaded through the normal system-DMA path are also recognized when
the MBA already exists in a supplied NAND image. The emulator tracks entry as
an application launch and a top-level `RETF` as an exit back to LD. Returning
does not mean “keep this frame on screen”; LD resumes and may launch the slot
again. While an MBA owns the inherited loader display, disabling both IRQ and
FIQ stalls acceptance of new scanout state and preserves the previously latched
frame. This reproduces the real-device white/frozen-screen failure that was
previously hidden by unconditional host framebuffer reads. The extra two-second
watchdog injection remains limited to an explicit `--mba` replacement, so stock
retail modules keep their native watchdog state.

The GPL16250VA PPU model follows the verified SDK register definitions:
`P_PPU_Enable` bit 0 is not treated as a global enable, frame-base mode is bit
7, and the RTC HMS registers at `0x7920..0x7922` now advance from emulated time
when `C_RTCEN` is set. RTC status/enable delivery and system-DMA completion
flags use their documented W1C paths.

PPU indexed and direct-color transparency, the four global blend levels,
per-sprite 6-bit blend values, RGB fade, and saturation are applied in the
renderer. Video comparison/wrap events, timers, timebases, RTC, watchdog, ADC,
USB suspend, and SPU beat events use cycle deadlines. Counter MMIO reads remain
cycle-exact, but the interpreter can skip peripheral work until an observable
event is due.

On the development Mac, the event scheduler changed a deterministic
10,000,000-instruction retail boot run from 26.7 to 35.3 MIPS without changing
its final cycle count, PC, or registers. A profile trained for 10,000,000
instructions reached about 44 MIPS. These figures are a regression reference, not
a portable guarantee; CPU and compiler versions matter.

This is an exact filesystem substitution, not a format-role converter. Retail
firmware can reject an otherwise valid bundle MBA when it occupies the main-menu
slot. For example, VTech's `BUNDLE_G1_135800G1.MBA` has the internal role label
`MGB_G1`; testing it with `--mba` falls back to the normal menu. An MBA intended
for direct startup must have the structure and entry behavior expected of an
`MM.MBA` application.

Host controls:

- Arrow keys: MobiGo D-pad and MobiGo 2 accelerometer tilt simultaneously
- Left or right Control: physical Primary button
- Letter keys: matching MobiGo keyboard keys
- Escape: physical Exit button
- F12: close the emulator
- Left mouse button: resistive touchscreen stylus

See `../docs/reference/INPUT_MATRIX.md` for the complete matrix and
all host bindings.

Headless tests can inject repeatable LCD touches with one or more
`--touch-event at,duration,x,y` options. The first two values are CPU
instruction counts; events are sorted by start time and may not overlap.

Headless keyboard-matrix tests can inject every documented matrix control with
`--key-event at,duration,key`. Use letter names or the logical names listed in
`../docs/reference/INPUT_MATRIX.md`.

The buttons drive the GPIO matrix cells that the retail firmware scans. Mouse
input drives the MobiGo board's IOE touch-contact circuit and the 12-bit manual
ADC channels used by its four-wire resistive panel. Neither path bypasses
firmware input processing.

The PPU renderer decodes sprite positions as signed ten-bit coordinates and
clips them at the 320x240 LCD boundary. This matches SY's centered Family-B UI
objects, including animations that leave the top of the display without
reappearing at the bottom.

USB device simulation is enabled with:

```sh
./build/mobigo2_emu --usb
```

Press `U` in the main window to open the host-control window. Connect/disconnect drives the board's
active-low IOC11 cable-detect input. Commands use USB Mass Storage Bulk-Only
Transport and SCSI sector reads/writes through the emulated USB and DMA
controllers; they do not edit NAND directly. The host locates the VTech private
command window from the MBR/FAT16 geometry in the same manner as the vendor
DLL. Flash reads and writes use the DLL's command/data sectors, and the firmware
performs the resulting NAND operations. Every write is then read back through
the vendor read command before the panel reports completion; protected or
rejected flash addresses report `FLASH WRITE VERIFY FAILED` instead of a false
success. Files are padded to the protocol's 512-byte sector boundary. Address
selection and file format still have to satisfy the retail firmware's region
handlers; the emulator deliberately does not bypass their validation. Both a
modified single-sector roundtrip and an existing ten-sector write/readback
beginning at flash address `0x00000000` have been verified to execute the
firmware's NAND erase/program path byte-for-byte.
Modified NAND is atomically saved back to the `--nand` image on a clean exit
from a `--usb` run.

In a windowed `--usb` run, USB remains disabled until `U` is pressed in the
main emulator window. That keypress opens the host-control window and enables
the emulated USB hardware; it is consumed rather than sent to the MobiGo
keyboard. The control window's **UPLOAD DEVICE FILE** action accepts a MobiGo
path such as `A:\BUNDLE\G1\135800G1.MBA` and a host input path. It performs the
recovered mailbox open/write/finalize/close sequence over the emulated USB
mass-storage transport, then reopens and reads the result back through the
firmware to verify its type, size, and complete contents. Existing files are
replaced and missing files use the recovered create flow; the NAND image is
never patched behind the guest firmware.

The external battery-monitor input defaults to a nominal `0x500` ADC level and
can be changed with `--battery-adc`; the retail firmware itself applies the
warning and shutdown thresholds.

For a deterministic headless boot-frame capture:

```sh
./build/mobigo2_emu --no-window --steps 50000000 --dump-frame build/frame.bmp
```

To run fast without a window first, then open SDL after a chosen instruction
count:

```sh
./build/mobigo2_emu --open-window-at 400000000
```

Experimental boot-source fuse values can be selected with `--efuse0`,
`--efuse1`, and `--efuse2`. The internal ROM uses `E-Fuse0 & 7` as a media
loader selector; the exact MobiGo 2 board value is still being identified.

Useful debug options:

```sh
./build/mobigo2_emu --boot spi-shim --no-window --steps 1000000
./build/mobigo2_emu --auto-app-handoff --no-window --steps 1000000
./build/mobigo2_emu --steps 200000 --trace
./build/mobigo2_emu --no-window --steps 1000000
./build/mobigo2_emu --rom internalrom.bin --rom-endian be --rom-shadow-low --no-window --steps 1000
./build/mobigo2_emu --allow-invalid-alu-nop --rom-fetch-mirror64 --no-window --steps 500000
./build/mobigo2_emu --no-window --steps 50000000 --dump-frame build/frame.bmp
./build/mobigo2_emu --no-window --steps 10000000 \
  --dump-memory build/runtime.bin --dump-memory-base 0x30000 --dump-memory-words 0x1000
./build/mobigo2_emu --no-window --steps 850000000 \
  --dump-memory build/framebuffer.bin --dump-memory-base 0x3fd400 \
  --dump-memory-words 76800 --dump-memory-dma --trace-start-insn 79000000
./build/mobigo2_emu --gpio-a 0xffff --gpio-b 0xfffe --gpio-c 0xffff \
  --no-window --steps 1000000
./build/mobigo2_emu --no-window --steps 30000000 --trace-pc 0x1140 0x1162 --trace-limit 200
```

Runtime diagnostics are written to `emulator.log`. Unknown opcodes halt
execution with register state. Unknown MMIO accesses are logged and return the
last written register value unless a better-documented behavior is implemented.
`--allow-invalid-alu-nop` is a temporary diagnostic workaround only; it treats
documented-invalid ALU opcode slots as no-ops and logs each use.
`--auto-app-handoff` and `--auto-menu-handoff` are also diagnostics only; they
force control-flow transitions that real firmware should eventually perform
itself through emulated hardware state.
