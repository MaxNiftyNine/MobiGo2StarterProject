# Resource graphs and audio formats

## Linked resource bundles

The current mutable bundle header is 32 words and begins with the version marker
`0x80000002`. It contains counts and tagged references to palette storage,
Family-A/Family-B descriptors, bitmap lookup data, and auto-instance state.

Tagged pointer classes include bundle-relative, primary-storage-relative, and
secondary-storage-relative forms. Registration rebases supported references in
place, so the graph must be writable.

## Family-A and Family-B

Family-A describes tiled background-style images. Family-B describes modes and
timed records containing position deltas, bounds, components, bitmaps, chunks,
palette selection, and private runtime storage.

Created objects are resident handles. Portable helpers can update known mutable
fields after the object pointer is retrieved through the resident API.

## Dynamic slots and text

Seven dynamic bundle slots are available in the recovered resident path.
Registering a clean generated font in a dynamic slot allows runtime glyph
objects without modifying the primary bundle. Unregistering destroys slot-owned
objects; callers must not keep stale handles.

## Audio roots

Title audio registration supplies a resource root and a patch root:

- W: a single waveform effect;
- S: an ordered sequence of child resource IDs;
- M: a compact stream of note, wait, control, program, auxiliary, and end events.

Patch roots map melodic programs or percussion notes to waveform zones,
transposition, loop, and envelope data.

## ADPCM36

An ADPCM36 stream uses frames of one header word and eight nibble-data words,
representing 32 samples, followed by the required stream terminator. Use the
provided encoder and preview rather than hand-authoring headers.

## Confidence

Core graph layouts and the maintained generated resources have deterministic
emulator coverage. Some rarely used descriptor/envelope fields remain unknown
because no independent caller establishes their meaning.
