# Firmware input set

The emulator expects a 128 KiB internal ROM, a 2 MiB SPI image, and the
reassembled 132 MiB stitched NAND. The two checked-in NAND parts combine to
138,412,032 bytes with SHA-256
`66e686225f709e07ca0d76b78b82374cb6fd27296c7a3d8b98c765da66442e7a`.

From the repository root:

```sh
python3 tools/nand/assemble_nand.py
```

This creates `vendor/firmware/nand.us-stitched.bin`, verifies its size and
hash, and leaves the numbered inputs unchanged. The assembled image is ignored
by Git and must not be committed.

`python3 tools/mobigo.py run` normally applies the built MBA as a transient,
role-aware overlay. `python3 tools/mobigo.py build --nand` creates a persistent
edited copy under `build/`; neither operation modifies the source firmware.

Firmware and device-derived images are not covered by the SDK license. Their
presence does not grant redistribution rights. Keep an untouched backup before
any storage experiment.
