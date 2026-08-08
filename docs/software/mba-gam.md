# MBA and GAM executable format

MobiGo `.gam` and MobiGo 2 `.MBA` files share the `bM_gbMQa` container family.
The repository builds complete SY and legacy G1 MBAs without opening a donor
application.

## Confirmed container structure

- eight-byte `bM_gbMQa` magic;
- little-endian multi-byte header fields;
- a `0x1000`-byte header/launcher region;
- a declared complete file size stored in words;
- word-addressed load and entry fields;
- a CRC-16/CCITT-FALSE over header bytes `0x00..0x3b`;
- title text, a 16-color RGB555 palette, and 64×104 4-bpp visible menu art;
- a profile-specific launcher footer occupying `0x0dc0..0x0fff`;
- a fixed-size address image whose internal zero ranges preserve runtime layout.

## Address conversion

For the observed MobiGo 2 profile family:

```text
runtime_base = body_load_word_address - 0x800
file_byte_offset = (runtime_word_address - runtime_base) * 2
```

This mapping is verified for known headers, entries, and examined executable
regions. It does not prove that every resource stays at its file-derived address
during execution.

## Launcher footer

The visible tile ends at `0x0dbf`. The remaining header bytes are structured
profile metadata, not extra pixels. Replacing them with art or zeros can let a
file be recognized but fail before its entry is called.

The builder synthesizes the complete selected footer and prevents a custom menu
tile from overwriting it.

## Builder

The routine project command is:

```sh
python3 tools/mobigo.py build
```

Direct packaging is available for pipeline diagnosis:

```sh
python3 tools/build/build_mba.py \
  --slot SY \
  --payload build/app.bin \
  --output build/MyGame.MBA
```

Most applications should use the SDK application builder or unified CLI so
compilation, entry patching, packaging, validation, and optional NAND install
remain one transaction.

## Unknown fields

Several header fields and individual footer mask meanings remain unknown.
Therefore the builder uses tested profiles rather than claiming a universal
arbitrary-role generator. Regional variants must be validated, not inferred
from one sample filename.
