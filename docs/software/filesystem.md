# Filesystem and application paths

The NAND contains MOBIGOFS data and recoverable snapshots. Applications normally
access it through resident file services; host tools manipulate disposable raw
images with filesystem-aware code.

## Resident path representation

The resident ABI packs two ASCII bytes into each 16-bit word. Public wrappers
accept ordinary C strings and perform that packing. Keep device prefixes and
backslash conventions as required by the resident path being opened.

## Supported operations

The SDK wraps open, close, read, write, truncate, absolute seek, size, a path
predicate that returns missing/file/directory, and remove behavior.

Existing-file operations have the strongest repeatable evidence. Fresh path
allocation reaches low-level NAND work, but new directory-entry publication is
not yet reliable across the emulator and tested physical workflow.

## Application-slot paths

Slot filenames vary by firmware region. Installation tools search the relevant
directory and replace the one existing filename ending in the selected slot
suffix. Do not put a literal regional prefix in an application build or agent
instruction.

## NAND host tools

Host installation preserves the source image, updates file metadata and
checksums, handles allocation, updates detected snapshots, converts logical data
back to raw pages, and reads the result back for exact comparison.

## Physical safety

On-device diagnostics should prefer known read-only files. Write, truncate,
remove, or experimental creation tests belong on copied NAND until the exact
publication and recovery behavior is established.
