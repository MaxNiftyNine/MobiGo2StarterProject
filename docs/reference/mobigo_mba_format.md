# MobiGo MBA/GAM executable format

This document describes the `bM_gbMQa` application container used by VTech
MobiGo `.gam` files and MobiGo 2 `.MBA` files. It is based on fourteen retail
files in the adjacent `MBAs` sample collection, cross-file comparison,
entry-point disassembly, menu-image decoding, and the existing MobiGo 2
homebrew research in this repository.

The format is only partly understood. Fields and rules below are marked
**verified**, **strongly inferred**, or **unknown** so that observations are
not presented as invented structure.

## Summary

- Both `.gam` and `.MBA` files use the same container and `bM_gbMQa` magic.
- Multi-byte header integers are little-endian.
- The first `0x1000` bytes form a fixed metadata and menu-art header.
- Addresses stored in the header are 16-bit **word addresses**, not byte
  addresses.
- Offset `0x08` stores the complete file size in words.
- Offset `0x14` stores the executable entry word address.
- Offset `0x18` stores the runtime word address corresponding to file offset
  `0x1000`.
- Offset `0x3c` stores a CRC-16/CCITT-FALSE of bytes `0x00..0x3b`.
- The header contains a title, a 16-color RGB555 palette, 64-by-104-pixel
  visible menu art, and a profile-specific launcher footer.
- No relocation, import, section, or resource table has yet been established.

## Numeric and address conventions

The Generalplus unSP CPU addresses 16-bit words. File offsets and sizes in this
document are bytes unless explicitly described as words.

Let:

```text
H = u32le(file + 0x18)       body load word address
B = H - 0x800                candidate runtime image base
F = byte offset in the file
W = runtime word address
```

The fixed header is `0x1000` bytes, or `0x800` words, so the observed mapping
is:

```text
W = B + F / 2
F = (W - B) * 2
```

This relationship is **verified** for the header, body boundary, all fourteen
entry points, and examined executable regions. Mapping the whole file this way
is useful as an initial static-analysis image, but it is not proof that every
later resource remains at that address during execution. Application or
loader code may decode, copy, bank, or overwrite later data.

All examined files have even byte lengths. The header's file-size value also
makes odd-byte files unrepresentable.

### Worked example: `BUNDLE_G1_135800G1.MBA`

```text
body load address H = 0x0c8800
runtime base B      = 0x0c8800 - 0x800 = 0x0c8000
entry address W     = 0x0e1a55
entry file offset F = (0x0e1a55 - 0x0c8000) * 2
                    = 0x334aa
```

The bytes at file offset `0x334aa` begin with a plausible unSP function
prologue. The same calculation lands on function-like code in every sample.

## Fixed header layout

The header occupies file offsets `0x0000..0x0fff`.

| Offset | Size | Meaning | Confidence |
|---:|---:|---|---|
| `0x00` | 8 | ASCII magic `bM_gbMQa` | Verified |
| `0x08` | 4 | Complete file size in 16-bit words | Verified |
| `0x0c` | 4 | Unknown | Unknown |
| `0x10` | 4 | Variant-dependent identifier or address-like value | Unknown |
| `0x14` | 4 | Executable entry word address | Verified |
| `0x18` | 4 | Word address at which file offset `0x1000` is loaded | Verified |
| `0x1c` | 4 | Unknown loader/platform field | Unknown |
| `0x20` | 4 | Unknown loader/platform field | Unknown |
| `0x24` | 4 | Unknown loader/platform field | Unknown |
| `0x28` | 4 | Unknown; commonly `0` or `0x6e0` | Unknown |
| `0x2c` | 16 | Zero in all examined files | Strongly inferred reserved |
| `0x3c` | 2 | Header CRC-16/CCITT-FALSE | Verified |
| `0x3e` | 2 | Zero in all examined files | Strongly inferred reserved |
| `0x40` | 64 | Variant-specific data; sometimes all zero | Unknown |
| `0x80` | 32 | NUL-padded ASCII title or application role | Verified |
| `0xa0` | 32 | 16 little-endian RGB555 palette entries | Verified |
| `0xc0` | 3328 | 64x104 indexed 4-bpp visible menu art | Verified |
| `0xdc0` | 576 | Profile-specific launcher resource footer | Verified for bundle/SY loading |
| `0x1000` | — | First byte of executable body | Verified |

The visible artwork ends exactly at the launcher footer:

```text
64 pixels * 104 pixels / 2 pixels per byte = 3328 bytes = 0x0d00
0x00c0 + 0x0d00 = 0x0dc0
```

### File size at `0x08`

The stored value is the size of the **entire file** in 16-bit words:

```text
actual file byte length = u32le(file + 0x08) * 2
```

This equality holds for all fourteen examined files.

### Field `0x10`

This field must not be assigned one universal meaning yet:

- In the four numbered `.gam` samples its values are `2`, `29`, `30`, and
  `31`, matching the product numbers in their filenames.
- In most MobiGo 2 system/bundle modules it contains one of
  `0x0f3e5a..0x0f3e62`, values which are address-like and are treated as
  protected callback boundaries by the earlier replacement-window tooling.
- The loading application is an outlier with `0x05eca204`.

It may be interpreted differently by different launcher generations or
application classes. The Ghidra loader therefore exposes it as `field_10`
without creating a function or reference from it.

### Fields `0x1c`, `0x20`, and `0x24`

The older-family files use address-like values:

```text
field_1c = 0x0c00de
field_20 = 0x1a00xx
field_24 = 0x2800ea
```

Most MobiGo 2 bundle modules instead use `0x0000ffff` sentinels in the first
two fields and `0x280642` in the third. These patterns imply loader or
platform parameters, but their operational meanings are not established.

## Header CRC

The stored little-endian 16-bit value at `0x3c` is calculated over exactly the
preceding 60 bytes, file offsets `0x00..0x3b`.

Parameters:

```text
width   = 16
poly    = 0x1021
init    = 0xffff
refin   = false
refout  = false
xorout  = 0x0000
```

Equivalent code:

```c
uint16_t mba_header_crc(const uint8_t header[0x1000])
{
    uint16_t crc = 0xffff;

    for (size_t i = 0; i < 0x3c; ++i) {
        crc ^= (uint16_t)header[i] << 8;
        for (unsigned bit = 0; bit < 8; ++bit) {
            crc = (crc & 0x8000)
                ? (uint16_t)((crc << 1) ^ 0x1021)
                : (uint16_t)(crc << 1);
        }
    }
    return crc;
}
```

All fourteen samples pass this check. The palette, title, menu art, footer, and
executable body are not covered by this CRC.

## Title, palette, menu art, and launcher footer

The title at `0x80` is a 32-byte NUL-padded ASCII field. It is a display name
in game files and often an internal role such as `MGB_SYS`, `MGB_TM`, or
`USB APP` in system modules.

The palette contains sixteen little-endian 16-bit entries:

```text
bit 15     transparency flag
bits 14:10 red
bits  9:5  green
bits  4:0  blue
```

The visible bitmap begins at `0xc0`. It is row-major, 64 pixels wide,
104 pixels high,
and uses one palette index per nibble. The high nibble is the left/first pixel
and the low nibble is the right/second pixel:

```text
byte = bitmap[(y * 64 + x) / 2]
index = (x & 1) ? (byte & 0x0f) : (byte >> 4)
```

Decoded samples produce recognizable launcher artwork, which independently
confirms the visible dimensions, nibble order, and palette placement.

### Launcher footer at `0xdc0`

The final `0x240` bytes of the fixed header were initially mistaken for
another eighteen rows of menu pixels. Normal-boot testing established that
MobiGo 2 bundle/SY launch code consumes this area as profile-specific launcher
data:

- replacing `0xdc0..0xfff` with ordinary pixels or zeroes caused SY to stop
  after its first header DMA and enter watchdog recovery;
- preserving the decoded SY footer while independently generating every
  visible pixel allowed the firmware to perform all three DMA stages, call
  entry `0x0dfc1d`, and execute the homebrew framebuffer code;
- the G1, G2, G3, G4, LD, SY, TM, and EBOOK files contain related structured
  patterns here, while the examined GAM, MM, and UB files use zeroes.

The MobiGo 2 bundle family begins the footer with:

```text
offset  little-endian u32
0xdc0   0x000c8000
0xdc4   0x003fd000
0xdc8   0x00075c00
0xdcc   0x00075fe0
0xdd0   0x000006ec
0xdd4   0x00000756
```

Later footer words form slot-specific masks and flags. Their individual
official meanings remain unknown, but the complete G1 and SY profiles are
synthesized explicitly by `tools/build/build_mba.py`; no source-container bytes are
read or copied.

## Executable body

The body starts at file offset `0x1000`, corresponding to the header word
address at `0x18`. The header entry address at `0x14` maps into this body using
the equation above.

The analyzed entries commonly start with bytes such as:

```text
88 da 48 20 08 0b 01 00
88 da 43 20 08 0b 01 00
```

With the community unSP language module, these decode as plausible function
setup code and Ghidra analysis proceeds from the computed entry address.

No general section directory has been identified. Consequently, the supplied
Ghidra loader creates two memory blocks:

```text
.mba_header  file 0x0000..0x0fff at runtime base B, read-only
.mba_body    file 0x1000..EOF    at header field 0x18, read/write/execute
```

The body permissions are intentionally permissive because code and resource
boundaries are not known. They do not imply that every body byte is executable
or writable on the physical device.

## Cross-sample results

Every row below has the correct magic, exact word-count size, valid header
CRC, and an entry that maps to plausible unSP code.

| File | Header title | Bytes | Runtime base | Body load | Entry | Entry file offset |
|---|---|---:|---:|---:|---:|---:|
| `58-115800-000-002_V020.gam` | `Wild Cards` | `0x47000` | `0x224000` | `0x224800` | `0x22d520` | `0x012a40` |
| `58-115800-000-029_V020.gam` | `Keyboard Jam` | `0x48000` | `0x224000` | `0x224800` | `0x22b03a` | `0x00e074` |
| `58-115800-000-030_V020.gam` | `DJ Beats` | `0x35000` | `0x224000` | `0x224800` | `0x22adc7` | `0x00db8e` |
| `58-115800-000-031_V010.gam` | `Monkey Disco` | `0x93000` | `0x224000` | `0x224800` | `0x22d88b` | `0x013116` |
| `BUNDLE_G1_135800G1.MBA` | `MGB_G1` | `0x214000` | `0x0c8000` | `0x0c8800` | `0x0e1a55` | `0x0334aa` |
| `BUNDLE_G2_135800G2.MBA` | `MGB_G2` | `0x13e000` | `0x0c8000` | `0x0c8800` | `0x0cff42` | `0x00fe84` |
| `BUNDLE_G3_135800G3.MBA` | `MGB_G3` | `0x3f0000` | `0x0c8000` | `0x0c8800` | `0x0d8445` | `0x02088a` |
| `BUNDLE_G4_135800G4.MBA` | `MGB_G4` | `0x2e2000` | `0x0c8000` | `0x0c8800` | `0x0d83e2` | `0x0207c4` |
| `BUNDLE_LD_135800LD.MBA` | `Loading App` | `0x1e000` | `0x0c8000` | `0x0c8800` | `0x0c889a` | `0x001134` |
| `BUNDLE_SY_135800SY.MBA` | `MGB_SYS` | `0x174000` | `0x0c8000` | `0x0c8800` | `0x0dfc1d` | `0x02f83a` |
| `BUNDLE_TM_135800TM.MBA` | `MGB_TM` | `0x13000` | `0x0c8000` | `0x0c8800` | `0x0ca0aa` | `0x004154` |
| `USENG_EBOOK.MBA` | `MGB_EBK` | `0x1d000` | `0x0c8000` | `0x0c8800` | `0x0d4908` | `0x019210` |
| `USENG_MM.MBA` | `Main Meun` | `0x41000` | `0x224000` | `0x224800` | `0x22d8a5` | `0x01314a` |
| `USENG_UB.MBA` | `USB APP` | `0x13000` | `0x224000` | `0x224800` | `0x226261` | `0x0044c2` |

The samples reveal two observed base/load families:

```text
MobiGo 2 bundle/EBOOK modules: base 0x0c8000, body 0x0c8800
older GAM plus MM/UB modules:   base 0x224000, body 0x224800
```

These are observations, not hard-coded format constants. A parser should
derive the base from the file's `0x18` field.

## Parser validation recommendations

A conservative reader or loader should require:

1. At least `0x1000` bytes and an even file length.
2. Exact `bM_gbMQa` magic.
3. `u32le(0x08) * 2` equal to the actual file length.
4. A body load address of at least `0x800` words.
5. An entry at or after the body load and inside the candidate mapped image.
6. Addresses fitting the unSP 22-bit word-address space.

CRC failure is valuable evidence of damage or an incomplete edit. A forensic
tool may still choose to import such a file with a warning; the supplied
loader records both stored and calculated values rather than rejecting the
file solely for a CRC mismatch.

AppleDouble sidecar files named `._*.MBA` or `._*.gam` are macOS metadata, not
application containers, and fail the magic check.

## Ghidra loader

The loader source is in:

```text
tools/ghidra/loader/MobiGoMbaLoader
```

Ghidra does not include an unSP language definition. Install the community
`ghidra-unSP` processor extension first:

<https://github.com/20051231/ghidra-unSP>

Then build the loader with `GHIDRA_INSTALL_DIR` pointing to an unpacked Ghidra
installation:

```sh
cd tools/ghidra/loader/MobiGoMbaLoader
gradle
```

Install the ZIP written to `dist/` using Ghidra's
**File > Install Extensions...** dialog and restart Ghidra. Import an MBA or
GAM normally; the detected loader name is **MobiGo MBA/GAM application**.

In addition to mapping and typing the container, the loader:

- creates the `mba_entry` external entry point;
- labels the title, palette, visible menu art, and launcher footer;
- records raw unknown fields and CRC status in Program Information;
- creates documented GPL16250/MobiGo 2 hardware and vector memory blocks; and
- labels PPU, system, NAND, GPIO, interrupt, timer, audio, USB, DMA, SPU, and
  vector addresses from this repository's hardware documentation.

The MMIO labels are analysis aids derived from the homebrew documentation,
not MBA header content.

## Remaining questions

Further runtime tracing or launcher disassembly is needed to determine:

- the meaning of header field `0x0c`;
- the exact per-variant semantics of field `0x10`;
- the meanings of fields `0x1c`, `0x20`, `0x24`, and `0x28`;
- the structure of variant data at `0x40..0x7f`;
- the individual meanings of the launcher-footer words and masks;
- whether any resource directory exists in the body;
- which body ranges are copied, decoded, banked, or overwritten; and
- whether other regional or firmware revisions introduce additional header
  variants.

Until those questions are answered, a new builder should use a tested
slot/firmware profile. The included generator constructs both profiles
deterministically; SY has passed the complete normal-boot emulator path, while
the G1 profile is structurally derived and still requires a from-scratch
menu-launch test.
