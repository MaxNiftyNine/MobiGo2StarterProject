# Executable examples

The examples exercise one recovered subsystem at a time through the official
resident runtime.

## Complete projects

- [`color_cycle/`](color_cycle/): minimal G1 framebuffer and system-DMA demo.
- [`bad_apple_player/`](bad_apple_player/): linked 1-bpp movie and PCM player;
  builds with original synthetic media or encodes user-supplied media.
- [`mobigo_celeste/`](mobigo_celeste/): advanced game port with packed graphics,
  input scanning, system DMA, and an optimized u'nSP assembly scaler.
- [`hardware_test_suite/`](hardware_test_suite/): guided SY-slot test of every
  currently supported SDK subsystem on real hardware.

Build the three G1 projects from the repository root with `make samples`, or
run the `build.py` in one project to build it alone. Every project uses the
standard SDK linker bodies and donor-free MBA packer.

## Focused probes

- `runtime_poll.c`: resident input and system-control polling.
- `resident_lifecycle.c`: setup/step/finalize callback contract.
- `system_ui_generated_boot_demo.c`: combined brightness/volume/off UI.
- `family_a_generated_boot_demo.c`: original family-A tiled background.
- `font_dynamic_boot_demo.c`: dynamic clean ASCII glyph bundle.
- `family_b_animation_boot_demo.c`: original two-record family-B timeline;
  record `0 -> 1`, X `80 -> 84`; used by `make animation-check`.
- `audio_pcm_const_boot_test.c`: const PCM8 W effect; `make audio-check`.
- `audio_sequence_boot_test.c`: ordered S children and repeat semantics.
- `audio_adpcm36_const_boot_test.c`: generated WAV-linked ADPCM36 W effect;
  `make adpcm-check`.
- `audio_music_multizone_probe.c`: two melodic programs, three melodic zones,
  direct percussion, four sequential M songs, automatic IRQ4;
  `make music-check`.
- `audio_music_adpcm36_probe.c`: generated ADPCM36 melodic zone with automatic
  IRQ4; `make music-adpcm-check`.
- `audio_music_aux_probe.c`: M classes 2/7/8 and scratch block transfer;
  `make music-aux-check`.
- `storage_*`: packed-path read, overwrite, create-path, and removal probes.

The generated examples use original artwork/audio and copy mutable resource
graphs to title RAM before registration. Large payloads remain const in the MBA.
