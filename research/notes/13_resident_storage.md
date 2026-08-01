# Resident file/storage runtime

This note documents the common resident file API used by retail MobiGo 2
applications. Names are clean-room working names. The strongest evidence comes
from SY application callers, the captured resident runtime, live banked file
backend code, and emulator runs against the stock NAND filesystem.

## Public service cluster

| Service | Working role | Evidence |
|---:|---|---|
| `0x075fa0` | storage/path configuration | SY path builder + resident decompile |
| `0x075fa2` | open file | retail callers + live backend |
| `0x075fa4` | close file | retail callers + live backend |
| `0x075fa6` | read bytes | retail callers + emulator verified |
| `0x075fa8` | write bytes | retail callers + emulator verified on existing file |
| `0x075faa` | truncate to current position | live backend + emulator verified |
| `0x075fac` | absolute byte seek | live backend + emulator verified |
| `0x075fae` | file size in bytes | live backend + emulator verified |
| `0x075fb0` | file stat/metadata | live backend, structure not public yet |
| `0x075fb2` | remove file | live backend + emulator verified |
| `0x075fb4` | path type/existence | live backend + emulator verified |

The low backend is banked. The `0x075fa2..fb4` wrappers eventually dispatch
through a live thunk table around `0x09377e`, whose observed concrete file
implementation is around `0x085d00..0x086328`.

## Path ABI

This was an important target-compiler trap.

The Generalplus compiler represents a C `char` in one 16-bit u'nSP word. The
resident filesystem does **not** consume that layout. It expects two 8-bit path
characters packed into each word, little-byte first:

```text
"A:DEGER\\MBASORT.LST"

word 0 = 0x3a41  /* A: */
word 1 = 0x4544  /* DE */
word 2 = 0x4547  /* GE */
word 3 = 0x5c52  /* R\\ */
...
```

The normalizer accepts an optional drive prefix, prepends a root backslash when
needed, and consumes at most fourteen packed words. The clean-room wrappers
therefore accept normal C strings and pack them before entering the resident
service.

The same packed-path rule applies to application `path_exists` and MBA launch
paths. Passing a normal target C string directly produces malformed paths.

Path lookup is case-sensitive in the observed filesystem. For example,
`A:DEGER\\MBASORT.LST` resolves while mixed-case `A:DEger\\...` does not.

Observed path predicate results:

- `0`: missing;
- `1`: file;
- `2`: directory/root.

## Handles

The file layer has four simultaneous public file slots. A returned 16-bit
handle contains a low-byte slot index and an 8-bit generation value. Close
increments the generation (wrapping while avoiding zero), so a stale handle is
rejected after its slot is reused.

One emulator regression observed:

```text
write open: 0x1500
close
read reopen: 0x1600
```

Both the slot bound and generation comparison are visible in the live backend.

## Read contract

`file_read(destination, byte_count, handle)` returns a 32-bit byte count or
`0xffffffff` on failure. A short read at EOF is normal.

Runtime verification against stock `A:DEGER\\MBASORT.LST`:

```text
path type:        1
handle:           0x1500
file size:        38
read at 0:        8 bytes, bytes matched stock file
seek absolute:    byte 32 -> 0
read at 32:       6 bytes, expected EOF-short data matched
close:            0
```

## Write/truncate contract

`file_write(source, byte_count, handle)` returns a 32-bit byte count or
`0xffffffff` on failure.

Open mode `2` enables the write-capable path. The top-level backend rejects it
when the mounted volume is not writable. The mode is not forwarded to the
lower directory-entry opener.

`file_truncate(handle)` truncates the file to its current byte position.
`file_seek_absolute(handle, offset)` sets the current byte position and rejects
offsets beyond EOF. `file_size(handle)` returns the byte length.

The clean regression overwrites a stock file only on a disposable NAND copy:

```text
exists before:    1
write handle:     0x1500
truncate at 0:    0
write:            8
size:             8
close:            0
exists after:     1
read handle:      0x1600
reopen size:      8
read:             8, exact payload match
seek to 4:        0
tail read:        4, exact payload match
close:            0
```

## Remove

`0x075fb2` removes an existing file. On a disposable copy of the stock NAND:

```text
exists before: 1
remove:        0
exists after:  0
```

The clean-room API exposes this as `mg_sdk_resident_storage_path_remove()`.

## Missing-file creation and emulator limitation

The lower opener at live address `0x07be99` has a clear missing-entry branch:
after resolving the parent directory, a lookup result of zero drives directory
record allocation, initializes a zero-length file object, writes a new entry,
and returns an open low-level handle. This is strong static evidence that the
firmware supports creating a missing file.

The current emulator cannot be used as the final proof for that branch. A
missing-file test causes substantially more NAND activity than overwrite:

```text
existing overwrite: 2 block erases, 125 page-program commands
missing-file path:   7 block erases, 325 page-program commands
```

The open handle, truncate, write count, and in-session size all succeed, but
the new path is not visible to a subsequent path lookup. When the emulator's
transient NAND state is forcibly saved, the external filesystem parser can no
longer recover the MobiGo logical-block OOB tags. Therefore this project does
not currently claim emulator-verified new-file publication.

`0x075fbe` was also tested as a possible publish/remount step because its
resident implementation selects the active storage backend, runs a
backend-specific operation, commits backend state, and recomputes volume
availability. In the missing-file probe it takes a long remount-like path,
returns `0xffff`, and the pathname remains missing. It is therefore **not**
the missing publication operation and is intentionally not exposed as a file
creation API.

This is an emulator/FTL verification limitation, not evidence that the retail
firmware lacks file creation. The static allocation path should be confirmed on
hardware or after the NAND controller/FTL emulation is made faithful enough to
preserve a create transaction.

## Clean-room implementation

Public declarations are in `include/mobigo_sdk/resident_storage.h`; target
wrappers are in `src/resident_storage.c`.

Useful validation commands:

```sh
make test
make target-check
make storage-check
```

`make storage-check` uses only copied NAND images. It never intentionally
modifies the stock source NAND.
