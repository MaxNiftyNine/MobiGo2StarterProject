# Starter application

Edit [`main.c`](main.c) to build your game. The checked-in example uses the
SDK lifecycle and generated system UI, including volume, brightness, and Off
button handling.

Build an MBA without launching the emulator:

```sh
python3 tools/build/build_sdk_app.py app/main.c \
  --output-dir build \
  --name MobiGo2Starter \
  --slot SY
```

Add `--install-nand --nand-output build/nand.edited.bin` to install the MBA in
a copy of the development NAND. The builder accepts repeatable
`--extra-source` arguments for generated assets and `--with-clean-font` for the
built-in 5x7 ASCII font.

The direct MBA handoff does not perform a normal initialized-data CRT copy.
Keep immutable graphics and audio `const`, and explicitly initialize mutable
state in a known title-RAM arena. The starter demonstrates that pattern.
