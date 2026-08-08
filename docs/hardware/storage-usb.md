# NAND, SPI, filesystem, and USB hardware

## SPI NOR

The console has a 2 MiB SPI NOR device used by early boot firmware. The verified
read path and command framing are modeled. General write/erase behavior is not a
supported application storage API.

SPI byte addresses are bytes even though CPU MMIO addresses are words.

## Raw NAND

The development NAND geometry is:

```text
2048 data bytes per page
64 spare bytes per page
64 pages per block
1024 blocks
132 MiB raw image including spare data
```

Emulator2 models command/address/data cycles and enough erase/program behavior
for firmware and copied-image workflows. NAND ECC and every FTL recovery rule
are not fully implemented.

Applications should use resident file services, not raw NAND commands.

## MOBIGOFS and snapshots

The filesystem tools preserve raw-page layout, record metadata, and detected
recoverable snapshots when installing an MBA. They read the installed file back
for exact verification. The source image remains unchanged.

## USB device path

Physical device tools communicate through the VTech mass-storage mailbox and
filesystem commands. They identify the expected MobiGo disk and discover slot
filenames. Emulator USB mode models enumeration, mass-storage transport, the
private command window, firmware-mediated reads/writes, and read-back checks.

Arbitrary USB classes and all host timing are not modeled.

## Safety boundary

Keep untouched dumps. Use disposable copies for write, truncate, remove, and
installation testing. A successful low-level write is not sufficient; reopen
and verify the complete contents through the same firmware-visible path.
