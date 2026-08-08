# Licensing, firmware, and device safety

The original SDK code and documentation are licensed under the repository's
`LICENSE`. That license does not automatically cover third-party compilers,
firmware, game code, media, trademarks, or device-derived data.

## Keep source categories separate

- Original SDK, tools, generated test art, and generated test audio may follow
  the repository license when their file notices say so.
- Generalplus toolchain components under `vendor/` retain their own terms.
- Firmware, NAND, SPI, ROM, and other device-derived binaries are not made
  redistributable merely by being useful to the emulator.
- Example ports may inherit upstream game/code/media terms. Review each
  example README before publishing binaries.

Do not commit retail executable bodies, extracted copyrighted art or audio,
device identifiers, credentials, or decompiler output containing substantial
proprietary code. Metadata such as hashes, offsets, sizes, call targets, and
independently written behavioral descriptions is the preferred research form.

## Safe test progression

1. Run host unit and authoring tests.
2. Build the target and validate it in both emulator modes.
3. Use a disposable copied NAND for filesystem mutation tests.
4. Run the guided physical test suite.
5. Install to the system slot only with verified recovery media and an
   untouched backup.

The system application is the canonical software target, but replacing the
physical system slot is still a high-risk deployment operation. The default
`python3 tools/mobigo.py run` workflow does not write a physical console.

## Device writes

- Let the USB installer discover the console's existing slot filename; never
  assume a regional numeric filename.
- Match the MBA target metadata to the selected slot.
- Keep the console powered and connected through the complete write and
  read-back operation.
- Never test deletion, truncation, fresh-file publication, or recovery theory
  on the only copy of device data.

See [Deployment and recovery](../guides/deployment.md) for commands and
[Source confidence](source-confidence.md) for research-reporting rules.
