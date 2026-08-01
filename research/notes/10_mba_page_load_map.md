# MBA physical page-load map

The MobiGo 2 launcher footer at file offset `0x0dc0` contains the section
mapping that was previously missing from the MBA format description. This is
loader metadata, not menu artwork.

All addresses below are 16-bit u'nSP word addresses. File offsets and page
sizes are bytes unless marked otherwise.

## Layout

The recovered fields are:

| File offset | Size | Meaning |
|---:|---:|---|
| `0x0dc0` | 4 | first word address represented by the bitmap |
| `0x0dc4` | 4 | exclusive end word address represented by the bitmap |
| `0x0dc8` | 4 | resident range start, observed `0x075c00` |
| `0x0dcc` | 4 | resident range end, observed `0x075fe0` |
| `0x0dd0` | 4 | unresolved, observed `0x000006ec` |
| `0x0dd4` | 4 | unresolved, observed `0x00000756` |
| `0x0dd8` | `52 * 4` | little-endian page bitmap |
| `0x0ea8` | `0x158` | reserved/profile data; zero in inspected MobiGo 2 files |

One bitmap bit represents `0x800` words, or `0x1000` file bytes. Bit zero is
the low bit of the first bitmap dword. Runtime page `n` begins at:

```text
runtime_page[n] = map_begin + n * 0x800 words
```

The loader walks set bits in ascending order. Consecutive `0x1000`-byte pages
from the MBA are assigned to those set runtime pages in the same order.
Therefore the file is a compact concatenation of populated physical pages;
gaps between mapped runs do not occupy file space.

For every inspected MobiGo 2 MBA:

```text
popcount(page_bitmap) == file_size / 0x1000
```

The four older GAM samples and MM/UB have a zero footer and retain the
previous linear mapping rule.

## Bundle mappings

| Title | File pages | Normal run | Primary asset run |
|---|---:|---|---|
| G1 | 532 | file `0x000000..0x077fff` -> `0x0c8000..0x103fff` | file `0x078000..EOF` -> `0x31b000..0x3e8fff` |
| G2 | 318 | file `0x000000..0x04dfff` -> `0x0c8000..0x0eefff` | file `0x04e000..EOF` -> `0x371000..0x3e8fff` |
| G3 | 1008 | file `0x000000..0x267fff` -> `0x0c8000..0x1fbfff` | file `0x268000..EOF` -> `0x325000..0x3e8fff` |
| G4 | 738 | file `0x000000..0x167fff` -> `0x0c8000..0x17bfff` | file `0x168000..EOF` -> `0x32c000..0x3e8fff` |
| SY | 372 | file `0x000000..0x06dfff` -> `0x0c8000..0x0fefff` | file `0x06e000..EOF` -> `0x366000..0x3e8fff` |

The asset run's physical start is exactly the far pointer passed as the
second argument to resident bundle-registration service `0x075f00`.

SY runtime tracing independently confirms the map. The firmware staged the
complete file, copied pages below file offset `0x06e000` to the normal image,
then copied the suffix in `0x800`-word DMA operations beginning at
`0x366000`. A chunk pointer `0x80014e60` resolves to physical word address
`0x37ae60`. Its 256 bytes occur at file offset `0x097cc0`:

```text
0x06e000 + 2 * 0x14e60 = 0x097cc0
```

## Shared standard bitmap

The complete first 32-by-32, two-bit-per-pixel brightness chunk is identical
in G1, G2, G3, G4, and SY. Its file position in each title obeys:

```text
file_offset = primary_run_file_offset
            + 2 * (primary-relative pointer & 0x3fffffff)
```

This is direct evidence that the official builds linked a shared SDK artwork
payload, in addition to sharing descriptor schemas and runtime behavior.
Only hashes and mapping metadata are retained in this clean-room project; no
retail bitmap bytes are copied.

## Padding

The page loader requires the file to contain whole `0x1000`-byte pages.
Zeroes immediately before the asset run are linker alignment padding in the
last normal page. They are not a hidden checksum or resource payload.

They can be reduced only by moving preceding content while preserving the
page boundary and regenerating the bitmap. The final MBA length must still be
page aligned, and every set bitmap bit must have one corresponding file page.

## Reproduction

`tools/re/inspect_mba_page_map.py` validates the bitmap, decodes physical runs,
and checks its population count against the complete file length.
`research/reports/mba-page-load-map.json` contains the metadata-only sample census.
