# Audio and storage

Audio and storage both cross the resident ABI. Add them after the basic
lifecycle, input, and rendering path is stable.

## Audio resource classes

The reconstructed audio model uses:

- **W** resources for individual PCM8 or ADPCM36 waveforms;
- **S** resources for ordered child-effect sequences;
- **M** resources for compact sequenced music commands and patch zones.

Resident registration returns handles used for playback and state operations.
Do not treat every low-level return register as a portable C boolean; use the
public wrapper's documented result and written state.

Convert a WAV to ADPCM36 with:

```sh
python3 tools/assets/build_adpcm36_audio.py \
  input.wav build/audio --prefix effect
```

Listen to the generated decoded preview and run the corresponding emulator
check before linking it into a game.

For the simpler physically established PCM8 W-resource path used by Homebrew
Launcher:

```sh
python3 tools/assets/build_pcm8_audio.py \
  input.wav build/audio-pcm --sample-rate 1800
```

The output stream is unsigned mono PCM8 with the resident/SPU terminator. Use
the manifest's byte, sample, and word counts when preparing the W record, and
set the resident `repeat` argument once for looping; do not continuously
retrigger a playing channel from the frame callback.

## Music timing

Sequenced M resources rely on the resident SPU beat scheduler. Applications
should register valid patch roots and let the resident advance music; do not
call an internal tick function from the game frame.

## Storage paths

Resident paths are packed as two ASCII bytes per 16-bit word by the SDK. Use the
path helper and public file operations instead of constructing packed buffers by
hand.

Existing-file open, size, read, seek, write, truncate, reopen, and remove paths
have repeatable copied-NAND coverage. Publishing a brand-new directory entry has
a weaker evidence boundary; see [Known limitations](../reference/known-limitations.md).

## Safety rules

- Run destructive storage tests only on disposable NAND copies.
- Keep physical diagnostic reads non-destructive unless recovery and the exact
  write path are understood.
- Close handles on every error path.
- Bound reads and writes using the file size and caller buffer capacity.
- Never use a regional system filename as general application storage.

## Application testing

Audio tests should verify handle creation, state transition, representative
output, stop/pause behavior, and natural completion. Storage tests should verify
contents after close and reopen, not only a successful return code.
