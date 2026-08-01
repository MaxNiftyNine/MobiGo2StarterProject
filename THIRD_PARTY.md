# Third-party and device-derived material

The MIT license in this repository applies only to original project source,
documentation, tests, and generated clean-room assets where the file does not
state another license. It does not relicense bundled third-party or
device-derived material.

The repository includes a Generalplus u'nSP compiler/toolchain and linker body
files for reproducible target builds. Those files remain subject to
Generalplus's terms. Verify that you have the right to use and redistribute
them before publishing a fork or release archive.

The firmware directory contains device-derived internal ROM, SPI, and split
NAND data for local emulation. VTech retains any applicable rights. Only use
firmware dumped from hardware you are legally entitled to use, and do not
assume that GitHub availability grants redistribution permission.

Emulator2 includes or dynamically uses SDL2 and contains its own third-party
license files. The Windows bundle also includes MinGW-w64's `libwinpthread` and
the GCC `libgcc` and `libstdc++` runtime DLLs. Their MinGW, GCC, LGPL, and GCC
Runtime Library Exception notices are adjacent to the binaries in
`emulator/bin/windows/`. The Ghidra loader source contains an Apache-2.0 notice
because it is built against Ghidra extension interfaces. Ghidra, ghidra-unSP,
Wine, MkDocs, and MkDocs Material are separate projects under their own
licenses.

The MobiGo Celeste sample is derived from Celeste Classic and the `ccleste` C
translation and includes game artwork needed by that technical port. It is not
relicensed by this repository's MIT license. Review the upstream projects and
rights before publishing or redistributing that sample.

The JSON reports and notes record clean-room observations such as hashes,
addresses, counts, and decoded structures. They do not embed retail executable,
artwork, or audio payloads. Historical `path` fields identify local sample
labels used during analysis and are not runtime dependencies.

Keep untouched recovery copies before editing or flashing NAND/SPI data.
