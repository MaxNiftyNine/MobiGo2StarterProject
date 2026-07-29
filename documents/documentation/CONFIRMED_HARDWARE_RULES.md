# Confirmed hardware rules

These are the differences that mattered when code worked in an emulator but
failed, froze white, or repeatedly returned to the loader on real hardware.

## The G1 MBA entry is an application callback

For the verified G1 profile, execution enters at word address `0x0E1A55`. It is not
a reset vector. A top-level `RETF` returns to the LD loader, which may relaunch
the slot. A resident program must deliberately remain active; a callback-style
program must return only when it intends to exit.

## Preserve inherited interrupt state

Do not begin by disabling both IRQ and FIQ. The retail launcher owns active
display services. Disabling inherited interrupts caused a frozen/white display
on hardware even when an emulator continued reading framebuffer memory.

## Service the watchdog

The loader can hand off with the watchdog active. Resident loops must write the
documented clear value to `0x780B` frequently, or deliberately configure the
watchdog with understood semantics. A hardware reset every few seconds usually
means this rule was missed.

## Use the live launcher framebuffer

Do not assume `0x018000` is a usable physical framebuffer in a launched MBA.
Read the launcher-selected FBI/FBO state and use the physical SDRAM display
buffer it configured. The confirmed color-cycle and Bad Apple paths use system
DMA for scanline/fill transfer.

## Generate the complete slot profile

The builder synthesizes the complete MBA. Keep the selected profile's
addresses, size, role, and launcher footer consistent:

```text
entry runtime word address     0x0E1A55
runtime/file word bias         0x0C8000
entry byte offset              (0x0E1A55 - 0x0C8000) * 2 = 0x334AA
next protected callback        0x0F3E5C
safe replacement bytes         149,518
```

The builder rejects payloads that do not fit this layout. SY uses its own
entry, footer, and size profile; changing a header entry does not relocate the
payload.

## Do not rely on C startup

The examples patch a tiny jump at the callback entry and enter `main` without
normal reset-time C initialization. Avoid initialized global/static state
unless you explicitly implement and verify data/BSS setup in memory you own.

## unSP addresses are word addresses

The CPU and linker use 16-bit word addressing. MBA file offsets are bytes.
Confusing the two introduces a factor-of-two error. The packer performs the
known conversion rather than searching for code heuristically.

## Audio requires the retail output gate

Writing samples to the DAC alone was silent on physical hardware. The recovered
retail setup sequence writes:

```text
0x78FF = 0x0000
0x78F0 = 0x3800
0x78F8 = 0x3000
0x78FF = 0x0001
```

The current experimental player also sets volume/envelope to `0x7F`. The
emulator models this gate, but physical V6 audio confirmation is still pending.
