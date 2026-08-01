# MBA and GAM executables

`tools/build/build_mba.py` creates complete G1 and SY MBA containers from a compiled
payload and recovered format metadata. It never opens a donor MBA.

## Known structure

- Eight-byte magic: `bM_gbMQa`.
- A 0x1000-byte launcher/header region.
- Little-endian 16-bit u'nSP words.
- Slot-specific load, entry, compatibility, and protected address windows.
- A 16-color RGB555 palette and 64×104 indexed 4-bpp launcher tile.
- A CRC-16/CCITT-FALSE header checksum.
- A fixed-size address image whose unused runtime windows are zero-filled.

The apparent blank space is intentional address padding. The loader and
firmware interpret offsets as locations in a fixed word-addressed image, so
removing interior zero ranges would move later code and compatibility data.

The detailed field table, offset formulas, page-map behavior, GAM variants,
and Ghidra mapping rules are in
`docs/reference/mobigo_mba_format.md` and
`docs/reference/mobigo2_mba_development_guide.md`.

## Direct packaging

```sh
python3 tools/build/build_mba.py \
  --slot SY \
  --payload build/app.bin \
  --output build/MyGame.MBA
```

Most projects should use `tools/build/build_sdk_app.py`, which performs compilation,
entry patching, packaging, and validation together.
