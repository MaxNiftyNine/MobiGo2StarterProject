# Resident audio runtime map

This early subsystem note is retained as an address-oriented index. The complete
current resource grammar, clean encoders, patch banks, sequencer commands, and
automatic SPU beat implementation are documented in
`research/notes/15_audio_resources_and_music.md`.

## Common services

- `0x075e06`: register title M/W/S root and optional patch root;
- `0x075e0e`: play W/S sound;
- `0x075e1a`: query sound state;
- `0x075e2c`: play M music;
- `0x075e32/34/36/38`: pause/resume/stop/state;
- `0x075e3c/3e/40`: repeat/get level/set level.

## Verified clean paths

- const PCM8 W effects;
- ordered/repeating S sequences;
- generated ADPCM36 W effects;
- compact M event authoring for classes 0 through 8;
- multiple melodic programs and upper-key zones;
- channel-9 direct percussion;
- PCM8 and generated ADPCM36 M zones;
- automatic SPU beat IRQ4 scheduling through the clean emulator patch.

Run `make audio-check`, `make adpcm-check`, `make music-check`,
`make music-adpcm-check`, and `make music-aux-check` for executable proofs.
