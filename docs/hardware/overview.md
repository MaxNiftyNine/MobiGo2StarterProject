# MobiGo 2 hardware overview

The MobiGo 2 is built around a Generalplus GPL16250-class 16-bit u'nSP SoC with
external SDRAM, SPI NOR, raw NAND, a 320×240 touch LCD, audio output, a keyboard
and button matrix, USB device connectivity, and a three-axis accelerometer.

## Confirmed board-level components

| Function | Observed component or geometry | Confidence |
| --- | --- | --- |
| SoC | Generalplus GPL16250 | Verified board marking/documentation |
| External RAM | EtronTech EM638165TS-6G, 4M×16 SDRAM | Verified component identification |
| SPI NOR | MX25L1606E-compatible, 2 MiB | Verified size and command behavior |
| NAND | 2,048-byte data + 64-byte spare pages, 64 pages/block, 1,024 blocks | Verified dump geometry |
| LCD | 3-inch 320×240 panel with resistive touch | Verified device behavior |
| Motion | Bosch-compatible path at I²C address `0x18`; alternate driver evidence exists | Emulator and firmware verified; board variants remain possible |

## Addressing rule

The CPU uses 16-bit **word addresses**. Address `0x1000` selects the word at byte
offset `0x2000` in a flat byte dump. MMIO constants are word addresses as well.

Storage protocols and file formats often use byte addresses. Every document and
API should label the unit when ambiguity is possible.

## Two programming layers

Most homebrew should use resident firmware services for lifecycle, input, UI,
audio, and storage. This preserves the console environment and avoids relying
on incompletely characterized registers.

High-performance framebuffer ports can use `hardware.h` for a conservative
low-level surface: inherited framebuffers, watchdog, DMA, and direct matrix
scanning. Direct MMIO beyond that layer is research work.

## Evidence boundary

The emulator is an executable hardware model, not automatic proof of the
physical chip. Pages in this section distinguish:

- behavior observed on hardware or in repeatable firmware paths;
- behavior implemented from datasheet, firmware, or related-chip evidence;
- registers that are only retained or remain unknown.

See [Source confidence](../reference/source-confidence.md) and the
[capability matrix](../testing/capability-matrix.md).
