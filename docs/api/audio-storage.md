# Audio and storage API

## Portable audio helpers

`audio.h` interprets resident playback states. `audio_resources.h` constructs
the clean-room resource structures used by effects and music.

The authoring API covers:

- PCM8 waveform banks and roots;
- ADPCM36 frame encoding and stream termination;
- W single effects;
- S child sequences;
- M headers, events, notes, waits, program/control changes, and end/repeat;
- melodic and percussion patch roots and zones.

Writers return failure rather than emitting a partial multiword event when
capacity is insufficient. Check every result.

## Resident audio

`resident_audio.h` registers title resources and provides play/state operations
for effects plus play, pause, resume, stop, state, repeat, and level operations
for music.

Handles are opaque 32-bit values. Use state wrappers instead of assuming a raw
resident return register is a portable boolean.

## Resident storage

`resident_storage.h` provides:

- ASCII-to-packed-path conversion;
- open and close;
- read and write;
- truncate and absolute seek;
- file size and path predicates;
- path removal.

`MG_SDK_INVALID_FILE_HANDLE` and `MG_SDK_FILE_IO_ERROR` are distinct failure
sentinels. Bound operations by both file size and buffer capacity, and close the
handle after a partial failure.

Fresh-file publication has a weaker evidence boundary than operations on an
existing path. Run write/create/remove experiments only against disposable NAND
copies.

See [Audio and storage](../guides/audio-storage.md).
