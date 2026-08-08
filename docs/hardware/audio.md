# DAC and SPU audio

The GPL16250 audio environment contains direct DAC FIFOs and a multi-channel SPU
used by resident sound and music resources.

## Supported high-level behavior

The SDK and emulator cover:

- direct PCM FIFO state;
- SPU PCM8 and PCM16;
- IMA ADPCM and the recovered ADPCM36 stream;
- pitch, pan, volume/envelope, looping, and channel completion;
- SPU beat scheduling used by resident music;
- IRQ/FIQ routing needed by refill and beat events.

Physical tests have produced audible homebrew PCM, sequences, ADPCM36, and
sequenced music. Exact analog characteristics, envelope edge cases, and every
ADPCM36 corner remain less certain than digital state transitions.

## Output gate

Physical hardware requires the retail-style output-enable sequence in addition
to feeding digital samples. Resident APIs and current low-level support own
that setup. A port should not reproduce an old four-register snippet unless it
also owns the complete audio environment.

## Completion semantics

Programmed channel enable and live channel status are different. Natural sample
completion clears live status and latches completion events without necessarily
erasing the programmed enable mask. This distinction matters to resident state
queries and scene progression.

## Music heartbeat

Resident M resources use the SPU beat registers and normal interrupt service to
advance commands. The emulator schedules the same hardware-visible events even
in silent/headless mode. Host audio output is optional; emulated audio state must
still advance when it is disabled.

## Evidence labels

Digital register/state behavior covered by `audio_test` is **Verified in the
emulator**. Audible formats exercised on a console are **Verified on tested
hardware**. Exact electrical output and untested codec combinations remain
**Unknown**.
