# MobiGo MBA/GAM loader for Ghidra

This extension imports the `bM_gbMQa` application format used by VTech
MobiGo `.gam` files and MobiGo 2 `.MBA` files.

It:

- selects the `unsp:LE:16:default` language;
- decodes the MobiGo 2 footer's 52-dword physical page-load bitmap;
- maps each compacted file-page run at its actual runtime word address;
- separates the 0x1000-byte metadata/menu-art header, executable code, and
  primary asset-storage runs;
- falls back to a linear mapping for older GAM and MM/UB files whose footer
  page map is absent;
- marks and names the MBA entry point;
- creates typed header, title, palette, visible menu-art, launcher-footer, and
  page-load-bitmap data;
- records header values and CRC status in Program Information;
- creates and labels the documented GPL16250/MobiGo 2 MMIO, video RAM, sound
  RAM, and interrupt-vector ranges.

The page map is validated by requiring one set bit for every `0x1000`-byte
file page. One bit represents `0x800` u'nSP words; set bits are visited
low-to-high while file pages are consumed sequentially. This recovers the
large physical gap between each title's linked code and primary bitmap/audio
payload without mapping the gap as invented bytes.

## Prerequisite

Ghidra does not ship with a Sunplus/Generalplus unSP processor module. Install
the community module first:

<https://github.com/20051231/ghidra-unSP>

The loader asks for its language ID, `unsp:LE:16:default`.

## Build and install

Set `GHIDRA_INSTALL_DIR` to an unpacked Ghidra installation, then run:

```sh
gradle
```

The extension ZIP is written below `dist/`. In Ghidra, use
**File > Install Extensions...**, add/install the ZIP, and restart Ghidra.
The build substitutes the target Ghidra release into `extension.properties`;
build a separate ZIP for each Ghidra release you support.

Import an `.MBA` or `.gam` normally. The detected format is
**MobiGo MBA/GAM application**.

## Analysis notes

The unSP processor uses 16-bit word addresses. Ghidra therefore displays the
same addresses as the hardware documentation: entry `0x0e1a55` is shown as
`0e1a55`, not byte address `0x1c34aa`.

The authoritative format notes are
[`docs/reference/mobigo_mba_format.md`](../../../../docs/reference/mobigo_mba_format.md).
