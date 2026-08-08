# CPU, addressing, and memory

## CPU family

The GPL16250 uses a 16-bit u'nSP-family core with a 22-bit word-address space,
segmented data/stack behavior, interrupt vectors, and far control transfers.
The bundled Generalplus toolchain is the supported target compiler/assembler.

The CPU-facing address space contains 4,194,304 16-bit word locations—8 MiB of
byte storage when fully backed.

## Word and byte conversions

```text
byte_offset = word_address * 2
word_address = byte_offset / 2
```

MBA executable entries and linker addresses are words. MBA file offsets and
container sizes are bytes. The build tools perform the known conversions; do
not search a binary for an address-shaped byte pattern.

## Practical memory map

| Word range | Role | Confidence |
| --- | --- | --- |
| `0x000000..0x006fff` | internal RAM / resident low memory | Verified firmware use; application ownership restricted |
| `0x007000..0x007fff` | peripheral registers | Verified MMIO window |
| `0x008000..0x027fff` | internal-ROM decoding region | Related documentation and boot behavior |
| `0x030000+` | external chip-select / SDRAM-backed space | Verified emulator and application behavior |

The exact decode and alias behavior of every upper range is not fully
characterized. Applications should use linker profiles and SDK memory constants
rather than manually placing sections.

## Title RAM

`memory_map.h` records the conservative range used by maintained SDK
applications and default reservations for standard UI/control state. It is not
a promise that all external RAM is free.

Resident firmware, its stack, loader state, framebuffers, and registered objects
remain live. Keep mutable application arenas within a documented project map and
check for overlap.

## Interrupt and stack state

An MBA entry inherits a live firmware environment. It is not a reset vector.
Disabling both IRQ and FIQ can stop display services that the launcher owns.
Preserve inherited state unless the application explicitly takes over a device
and has a tested replacement path.

## Instruction-set references

Bundled vendor manuals and datasheets may have redistribution restrictions and
are excluded from the public website. The emulator CPU implementation and
target compiler output are executable references; unusual instruction behavior
should receive a focused test before being documented as physical fact.
