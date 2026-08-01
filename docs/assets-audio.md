# Graphics and audio

The SDK generators emit deterministic binary data, C arrays, headers, and JSON
manifests. Generated assets are original and do not copy retail payload bytes.

## Graphics

Create the built-in system UI or clean ASCII font with:

```sh
python3 tools/assets/build_system_ui_bundle.py build/system-ui
python3 tools/assets/build_clean_font_bundle.py build/font
```

Other generators cover a Family-A background, standard settings/off overlays,
and Family-B sprite animation. The matching examples show how to copy mutable
bundle graphs into RAM, register them, and create resident objects.

Family-A is suited to background-style images. Family-B supplies object-based
sprites and animations. Version-2 bundles support relocations and dynamic
resource slots, including runtime text glyphs.

## Audio

Convert a WAV effect into the recovered ADPCM36 format:

```sh
python3 tools/assets/build_adpcm36_audio.py input.wav build/audio --prefix effect
```

The output includes C/header files, the packed stream, a manifest, and a
decoded WAV preview. Link the generated C with `--extra-source`.

The API supports PCM8 effects, ADPCM36 effects, chained effects, sequenced
music, patch zones, percussion, and auxiliary events. Music timing uses the
SPU beat interrupt. Physical hardware supplies that behavior; the repository
emulator implements the same timer directly and covers it with CTests and
runtime regressions.

## Add generated source

```sh
python3 tools/build/build_sdk_app.py app/main.c \
  --output-dir build \
  --name MyGame \
  --extra-source build/audio/effect_resources.c
```

Use the exact generated filename printed by the generator. Its parent directory
is automatically added to the compiler include path.
