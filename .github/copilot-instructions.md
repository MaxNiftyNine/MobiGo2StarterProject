# MobiGo 2 repository rules

Read `/AGENTS.md` before changing this repository; it is the canonical agent
contract.

- Use `python3 tools/mobigo.py` for normal build, run, doctor, and test work.
- New applications target `system`/SY. G1 is a legacy opt-in and must never be
  inferred from an old sample or research path.
- Edit `app/main.c`. Use public APIs from `include/mobigo_sdk/`; do not copy raw
  MMIO constants when the SDK provides the operation.
- A direct MBA entry has no conventional C startup. Do not rely on initialized
  writable globals or cleared BSS.
- Preserve standard Volume, Brightness, and Off behavior, and verify the result
  in Emulator2 before claiming it works.
- Never edit the only NAND/SPI image or install an MBA into a different target
  profile. Use transient overlays or a copied NAND.
- Treat `research/` and excluded legacy documentation as evidence, not current
  build instructions.
