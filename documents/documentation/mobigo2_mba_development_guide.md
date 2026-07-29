# MobiGo 2 from-scratch MBA development guide

This guide describes the active homebrew workflow. The toolkit generates a
complete `bM_gbMQa` container from a linked unSP payload and deterministic
slot-profile metadata.

For the byte-level format, confidence labels, and all fourteen analyzed
samples, read [mobigo_mba_format.md](mobigo_mba_format.md).

## Build model

The default target is the boot-time SY slot:

```text
runtime image base     0x0c8000 words
body load address      0x0c8800 words
application entry      0x0dfc1d words
entry file offset      0x02f83a bytes
compatibility address  0x0f3e60 words
payload capacity       164,998 bytes
complete file size     0x174000 bytes
header role            MGB_SYS
```

The generator creates every byte. Its inputs are the payload, an optional
palette, and optional visible menu art.

## Container construction

`tools/build_mba.py` performs these operations:

1. selects a G1 or SY slot profile;
2. allocates the profile's complete file size;
3. writes the magic and little-endian loader fields;
4. writes a slot-compatible header role;
5. generates an original RGB555 palette and 64x104 4-bpp `HB` tile unless
   replacements are provided;
6. synthesizes the profile-specific launcher footer at `0xdc0..0xfff`;
7. places the payload at the entry's calculated file offset;
8. writes an original far-jump trampoline at the address-like `0x10` field;
9. calculates CRC-16/CCITT-FALSE over header bytes `0x00..0x3b`; and
10. writes and reads back the finished MBA.

No executable, artwork, resource, or header bytes are sourced from another
application container.

## Why the launcher footer matters

The fixed header does not consist entirely of pixels after offset `0xc0`.

```text
0x00c0..0x0dbf  64x104 visible indexed artwork
0x0dc0..0x0fff  slot-profile launcher footer
```

An earlier 64x122 interpretation rendered the footer as plausible-looking
pixel noise, but normal boot exposed the distinction. A generated SY image
with ordinary pixels or zeroes in the footer was recognized and DMA-loaded
once, then the firmware entered watchdog recovery before calling its entry.

With the decoded SY footer synthesized at the correct offsets, the same
independently generated header art and executable body passed:

```text
first SY header DMA
second SY header DMA
final runtime-image DMA
MBA application entry at 0x0dfc1d
framebuffer DMA from homebrew code
```

This is the decisive evidence that the active builder no longer needs an
existing MBA while still following the retail launch path.

## Payload contract

The compiler and linker use 16-bit word addresses. MBA file offsets are bytes:

```text
runtime_base = body_load - 0x800
file_offset = (runtime_word_address - runtime_base) * 2
```

The payload must already be linked for its selected entry. The packager does
not relocate absolute calls, data references, or linker-generated tables.

The included build:

- links directly at the SY entry;
- replaces the first two words with a far jump to `main`;
- avoids normal reset-time C initialization;
- keeps IRQ and FIQ enabled;
- services the inherited watchdog;
- uses launcher-selected FBI/FBO buffers; and
- remains resident rather than returning accidentally.

Avoid initialized global/static data unless startup code explicitly copies
data and clears BSS in memory the application owns.

## Building

macOS:

```sh
MOBIGO_NO_LAUNCH=1 ./build_and_run.command --no-audio
```

Windows:

```powershell
.\build_and_run.ps1 -NoLaunch -NoAudio
```

Manual packaging:

```sh
python3 tools/build_mba.py \
  --slot SY \
  --payload build/app.bin \
  --output build/MobiGo2Starter.MBA
```

The command rejects empty, odd-length, or oversized payloads and reports the
base, load address, entry, capacity, CRC, and SHA-256.

## Custom launcher art

The default tile is original generated artwork. To replace it, supply:

```sh
python3 tools/build_mba.py \
  --slot SY \
  --payload build/app.bin \
  --palette path/to/palette.rgb555 \
  --menu-tile path/to/tile.4bpp \
  --output build/Custom.MBA
```

Requirements:

- palette: exactly `0x20` bytes, sixteen little-endian RGB555 words;
- visible tile: exactly `0xd00` bytes, 64x104 pixels, two pixels per byte;
- high nibble is the first/left pixel;
- palette bit 15 marks transparency.

The builder appends the slot footer; callers cannot accidentally overwrite it
through `--menu-tile`.

## NAND installation

The MBA is a normal file inside MOBIGOFS3.0. Use the filesystem-aware
installer:

```sh
python3 tools/install_mba_in_nand.py \
  firmware/nand.us-stitched.bin \
  build/MobiGo2Starter.MBA \
  build/nand.edited.bin \
  --slot SY
```

It preserves the source, updates file indexes and record checksums, handles
allocation if needed, updates every detected snapshot, converts logical data
back to raw NAND pages, and reads the installed file back for exact
verification.

## Validation

For the active SY build, require:

- generator unit tests pass;
- header magic, declared size, CRC, load address, and entry validate;
- Ghidra imports and analyzes the generated image;
- MOBIGOFS read-back equals the generated MBA;
- the emulator observes the SY header through normal system DMA;
- execution reaches `0x0dfc1d`;
- homebrew framebuffer DMA occurs; and
- no watchdog/system reset occurs during handoff.

The current from-scratch SY build passes all of those emulator checks.
Physical-device confirmation remains outstanding.

## G1 status

The G1 profile is generated from cross-sample header and footer analysis and
uses:

```text
entry              0x0e1a55
entry file offset  0x0334aa
capacity           149,518 bytes
file size          0x214000 bytes
```

It passes structural, CRC, and Ghidra validation. A payload for G1 must be
linked at `0x0e1a55`. The new profile still needs a complete from-scratch
Hamster Highway menu-launch test before it should be described as confirmed.

## Known unknowns

The generator is profile-driven because several official meanings remain
unknown:

- header field `0x0c`;
- the general semantics of field `0x10`;
- fields `0x1c`, `0x20`, `0x24`, and `0x28`;
- individual launcher-footer word and mask meanings; and
- possible regional or firmware variants.

Those gaps do not prevent deterministic SY construction for the verified
profile, but they do prevent claiming a universal arbitrary-role MBA builder.
