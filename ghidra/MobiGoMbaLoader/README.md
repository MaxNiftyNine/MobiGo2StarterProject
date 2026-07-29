# MobiGo MBA/GAM loader for Ghidra

This extension imports the `bM_gbMQa` application format used by VTech
MobiGo `.gam` files and MobiGo 2 `.MBA` files.

It:

- selects the `unsp:LE:16:default` language;
- maps the complete file as a candidate linear initial image, anchored by the
  verified header, body-load, and entry addresses;
- separates the 0x1000-byte metadata/menu-art header from the executable body;
- marks and names the MBA entry point;
- creates typed header, title, palette, visible menu-art, and launcher-footer data;
- records header values and CRC status in Program Information;
- creates and labels the documented GPL16250/MobiGo 2 MMIO, video RAM, sound
  RAM, and interrupt-vector ranges.

The loader deliberately does not invent relocation, import, or resource
tables. None were established in the analyzed samples. The linear mapping is
exact for the header and verified executable windows. Treat it as a static
file-image view for later resource data, which application or loader code may
decode, copy, bank, or overwrite.

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

Import an `.MBA` or `.gam` normally. The detected format is
**MobiGo MBA/GAM application**.

## Analysis notes

The unSP processor uses 16-bit word addresses. Ghidra therefore displays the
same addresses as the hardware documentation: entry `0x0e1a55` is shown as
`0e1a55`, not byte address `0x1c34aa`.

The authoritative format notes are
[`documents/documentation/mobigo_mba_format.md`](../../documents/documentation/mobigo_mba_format.md).
