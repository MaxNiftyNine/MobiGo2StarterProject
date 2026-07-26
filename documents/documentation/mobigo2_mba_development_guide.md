# From C to a Retail-Loadable MobiGo 2 MBA

> **Historical snapshot (2026-07-14):** this long-form record predates the
> final physical-hardware color-cycle and Bad Apple video confirmation, plus
> the later retail audio-gate work. Use `STATUS_MATRIX.md` and
> `CONFIRMED_HARDWARE_RULES.md` as the current authority.

## A donor-based build, packaging, and verification workflow

Companion to the *MobiGo 2 Programmer's Guide*  
Reverse-engineering record and practical build guide  
Revision 1.0 - 2026-07-14

---

## Purpose and scope

The archived [MobiGo 2 Programmer's Guide](archive/mobigo2_programmers_guide.pdf) explains the GPL16250-class execution model, word-addressed memory, display hardware, input, timers, DMA, storage controllers, audio, and the general emulator workflow. This companion deliberately does not repeat those subjects. The archive predates the final hardware work; use it as background, not as the status authority.

This document starts where that guide stops: with C source that already knows how to use the hardware, and ends with an MBA file that the retail MobiGo 2 menu can load from a bundle slot. It documents the exact process used to build and verify the working Bad Apple replacement for the G1/Hamster Highway slot.

The covered topics are:

- the difference between a flat unSP executable, an MBA container, a MOBIGOFS file, and a raw NAND image;
- the verified parts of the `bM_gbMQa` MBA header;
- how to derive the runtime entry and file patch offsets for the G1 donor;
- how to link C at the retail loader's real word address with the Generalplus tools;
- how to flatten an S37 linker result without accidentally retaining a 64K-word vector gap;
- how to place code and assets inside a loader-safe part of a donor MBA;
- why inherited interrupts must be handled at the module handoff;
- how to rebuild the MBA without changing its declared size or header CRC;
- how to install it in MOBIGOFS without modifying the source NAND;
- how to automate the retail menu path and prove that the application advances over time;
- failure signatures, their actual causes, and the checks that catch them.

This is not an official VTech or Generalplus specification. It is a reproducible reverse-engineering result for the supplied firmware, NAND, emulator, donor MBA, and Generalplus toolchain.

## What this method is - and is not

The successful Bad Apple file was not produced by inventing every MBA table from scratch. It was produced by using a real G1 MBA as a donor, preserving the retail loader-facing structure, and replacing a verified linear executable window with a payload linked for the same runtime address.

That distinction matters:

1. A flat `.bin` can contain valid unSP instructions and still be unusable as an MBA.
2. A file can have the right MBA magic and header CRC but still have the wrong role for a menu slot.
3. An MBA can be structurally valid but fail because its code was linked for a different address.
4. An MBA can reach its entry and then fail because retail interrupt state was inherited.
5. An MBA can be accepted by the loader but have later resource sections transformed instead of linearly mapped.

The donor method avoids pretending that the still-unknown chunk, relocation, import, and resource rules are solved. It preserves those rules byte-for-byte where the loader needs them.

For this guide, **retail-loadable** means the following acceptance test passed in the emulator:

- the edited NAND boots through the ordinary retail firmware;
- the automated touchscreen selects Hamster Highway;
- a second touch selects Easy;
- the firmware calls the G1 MBA entry at word address `0x0E1A55`;
- the replacement code takes control;
- inherited interrupts do not restore the loading screen;
- multiple later framebuffer captures contain different clean black-and-white frames.

Physical hardware execution has not yet been confirmed. The build is designed around real MBA samples and the retail firmware path, but emulator success is not a substitute for a device test.

## Confidence notation

Statements in this document use four informal confidence levels:

- **Verified:** directly checked against the supplied retail MBAs, linker output, NAND read-back, emulator trace, or frame captures.
- **Strong inference:** supported by repeated structure and observed loader behavior, but the field's official name is unknown.
- **Donor-specific:** true for the verified G1 donor and not safe to copy to another module without repeating the analysis.
- **Unknown:** preserved because changing it is not justified.

## The four layers of a launchable application

It is useful to keep four different artifacts mentally separate.

### 1. The linked unSP program

This is the code and statically addressed data produced by the Generalplus compiler, assembler, and linker. Every absolute function, global, and asset reference assumes a runtime **word address**. The existing programmer's guide explains that address model; this document only uses it.

The linker output in the working build is Motorola S37 text. It is not directly an MBA and it is not yet the final flat payload.

### 2. The flat payload

The S37 records are flattened relative to the module's runtime base. The payload starts with a tiny handoff:

```text
word 0: 0xF140                 ; INT OFF
word 1: 0xFE80 | main[21:16]   ; GOTO A22 opcode
word 2: main[15:0]             ; GOTO low word
```

The rest contains linked program bytes, padding, and encoded assets. This payload is only meaningful when copied into the donor's linear code window and loaded at the address used during linking.

### 3. The MBA file

The MBA is the retail module container. It contains a `bM_gbMQa` header, loader-facing fields, executable material, and resource data. The working method keeps the donor's header, size, title, role, and all bytes outside the replacement window.

### 4. The MOBIGOFS file inside raw NAND

The MBA is stored as a normal file in the translated MobiGo filesystem. For G1 in the verified NAND, the path is:

```text
/BUNDLE/G1/135804G1.MBA
```

Other dumps use names such as `135800G1.MBA`. The directory name and existing filename should be treated as firmware/region-specific. Replace the file already present in the intended slot; do not assume the numeric suffix is universal.

The raw NAND additionally contains page spare/OOB data, logical-block tags, page ordering, filesystem record wrappers, and record checksums. Copying MBA bytes into an arbitrary raw NAND offset is not equivalent to replacing a MOBIGOFS file.

## Evidence base

The format work was checked against these real files:

```text
an authorized local copy of the reverse-engineering dump
  misc/mobigo_system_files_11584/
```

That directory contains G1 through G4, Loading, System, TM, EBook, main-menu, and USB MBAs. All ten inspected files:

- start with `bM_gbMQa`;
- declare their size in 16-bit words at offset `0x08`;
- have an actual byte length equal to twice that word count;
- contain a header CRC at `0x3C` that matches the recovered algorithm;
- contain a readable role/title string beginning at `0x80`.

The G1 donor extracted from the emulator NAND and the real `BUNDLE_G1_135800G1.MBA` sample have identical headers and lengths. They differ at only two individual byte positions in the entire 2,179,072-byte file. This is strong evidence that the donor is a retail G1 variant rather than a synthetic look-alike.

## The verified MBA header

The following table describes only what is supported by evidence. Names such as `entry` are functional labels, not official symbols.

| Offset | Size | G1 value | Interpretation |
|---:|---:|---:|---|
| `0x00` | 8 | `bM_gbMQa` | Verified MBA magic. A second magic, `bM_gdSQl`, exists in the analysis tooling but was not used here. |
| `0x08` | 4 | `0x0010A000` | Verified file size in 16-bit words. G1 therefore occupies `0x214000` bytes. |
| `0x0C` | 4 | `0x0003BC0B` | Unknown module-specific field. Preserve it. |
| `0x10` | 4 | `0x000F3E5C` | Strongly inferred loader callback/reference. Adjacent retail modules use sequential values. Overwriting the corresponding region broke startup. Preserve it. |
| `0x14` | 4 | `0x000E1A55` | Verified G1 application handoff/entry word address. Emulator trace observed an indirect call to this exact value. |
| `0x18` | 4 | `0x000C8800` | Verified loaded linear image base associated with file offset `0x1000`. |
| `0x1C` | 4 | `0x0000FFFF` | Unknown sentinel. Preserve it. |
| `0x20` | 4 | `0x0000FFFF` | Unknown sentinel. Preserve it. |
| `0x24` | 4 | `0x00280642` | Common value in the retail bundle modules. Exact role unknown. Preserve it. |
| `0x3C` | 2 | `0xA4D3` | Verified header CRC for this G1 header. |
| `0x80` | up to 32 | `MGB_G1` | Human-readable module role/title. This is part of slot identity and is preserved. |

The real samples show why a generic field name must be used cautiously. Main-menu and USB MBAs use a different load family (`0x224800`) while the bundle modules use `0x0C8800`. G1, G2, G3, and G4 have different entries and sizes. A constant that works for G1 is not automatically a format-wide rule.

### Header CRC algorithm

The verified CRC is CRC-16/CCITT with polynomial `0x1021` and initial value `0xFFFF`, processed over bytes `0x00` through `0x3B` in file order. The implementation groups input into little-endian words but feeds each word's low byte and then high byte to the normal bytewise CRC update.

Equivalent Python:

```python
def mba_header_crc(data: bytes) -> int:
    crc = 0xFFFF
    for offset in range(0, 0x3C, 2):
        low = data[offset]
        high = data[offset + 1]
        for byte in (low, high):
            crc ^= byte << 8
            for _ in range(8):
                if crc & 0x8000:
                    crc = ((crc << 1) ^ 0x1021) & 0xFFFF
                else:
                    crc = (crc << 1) & 0xFFFF
    return crc
```

This calculation matched the stored CRC in all ten inspected retail MBAs.

No verified whole-file content CRC was encountered in the successful G1 substitution. Because the donor header was not changed, its CRC remained valid without recomputation. If any header byte from `0x00` through `0x3B` is changed, offset `0x3C` must be updated. That does not imply that every other integrity mechanism in every MBA type is known.

## Deriving the G1 executable window

This is the key technical result behind the working MBA.

### Linear mapping in the executable region

Runtime dumps and file comparisons established this donor-specific relationship for the G1 executable region:

```text
runtime_word_address = 0x0C8000 + file_byte_offset / 2
```

The header's `0x18` value helps confirm it:

```text
file offset 0x1000
0x0C8000 + 0x1000 / 2 = 0x0C8800
```

That equals the stored G1 base value `0x0C8800`.

The inverse mapping is:

```text
file_byte_offset = (runtime_word_address - 0x0C8000) * 2
```

Applying it to the verified entry:

```text
entry runtime address = 0x0E1A55
entry file offset     = (0x0E1A55 - 0x0C8000) * 2
                      = 0x334AA
```

The odd runtime word address is valid. The byte offset remains even because every word occupies two file bytes.

### The conservative upper boundary

G1's header field at `0x10` contains `0x0F3E5C`. Its exact official purpose is unknown, but three observations make it a necessary boundary:

1. The value points into the same linear address family.
2. Related modules use adjacent values (`0x0F3E5D`, `0x0F3E5E`, and so on), consistent with loader dispatch/callback entries.
3. A test that overwrote through this area failed before the replacement entry could run, while a payload ending before it launched successfully.

For the donor method, it is therefore treated as the first protected address after the replaceable entry window:

```text
protected runtime address = 0x0F3E5C
protected file offset     = (0x0F3E5C - 0x0C8000) * 2
                          = 0x57CB8
```

The usable byte capacity is:

```text
0x57CB8 - 0x334AA = 0x2480E = 149,518 bytes
```

The final Bad Apple payload is 129,962 bytes, leaving 19,556 bytes of margin before the protected boundary.

This does **not** prove that every byte in the window is generic application storage, nor that the same derivation works for G2, G3, MM, or arbitrary cartridge MBAs. It proves that replacing this window in this G1 donor, while preserving everything else, passes the retail load path.

### Why the later resource area was not used

An early attempt linked the payload at `0x110000` and placed its bytes at the file offset predicted by extending the linear mapping. The entry redirect worked, but execution reached transformed G1 image data rather than the payload.

The lesson is important: the simple file-to-runtime formula is verified for the executable region, not for the entire MBA. Later resource sections can be decoded, copied, banked, or otherwise transformed by loader tables. Do not hide executable code in an apparently corresponding later file offset unless runtime memory proves that the bytes survive unchanged.

## Toolchain and project contract

The successful build used the Windows Generalplus tools installed at:

```text
C:\Program Files (x86)\Generalplus\unSPIDE_4.1.1
```

Observed tool versions:

- C compiler (`udocc.exe`): 1.1.5;
- assembler (`xasm16.exe`): 1.14.19;
- linker (`xlink16.exe`): 1.14.13.18;
- C macro library: `library\CMacro\CMacro1232.lib`.

The verified project is:

```text
the `examples/bad_apple_player` project on the Windows build computer
```

Important files:

```text
MaxFun/
  main.c
  MaxFunG1.bdy
  tools/
    build.ps1
    encode_video.py
    srec_to_bin.py
  assets/
    source.mp4
  build/
    main.asm
    main.obj
    MaxFun.map
    player.s37
    player.bin
    movie.dat
    bad_apple.bin
```

The build is reproducible from `main.c`, the body file, the tools, and the source asset. Files under `build/` are outputs.

### C and C++ expectations

The demonstrated compiler path is C. A C++ source can only be treated as supported after the installed Generalplus compiler successfully accepts it and the required runtime is linked. Until then, use C or a deliberately freestanding C++ subset with no exceptions, RTTI, dynamic initialization, standard library dependency, or heap assumption.

For a C++-style architecture without relying on a C++ runtime, a practical approach is:

- expose the hardware abstraction as C functions and plain structs;
- use `.cpp` only for compile-time organization if the compiler supports it;
- provide `extern "C"` for the entry-facing ABI;
- avoid global constructors and destructors;
- inspect the linker map for unexpected runtime helpers;
- confirm every unresolved symbol is intentional.

The MBA packaging method is language-independent after linking. What matters is that the resulting machine code is position-correct, self-contained, and fits the verified window.

## Linking at the retail entry

The module is not a reset image and should not be linked at a convenient cartridge address such as `0x50000`. Retail firmware calls the G1 entry at `0x0E1A55`; every absolute code and data address must agree.

The working body file is:

```text
[ARCH]
BODY=GPL16250VA_CS0SRAM;
SEC=RAM,0,6FFF,W;
SEC=I/O,7000,7FFF,W;
SEC=SysROM,8000,17FFF,W;
SEC=FrameBuffer,18000,2FFFF,W;
SEC=Flash,E1A55,F1A44,F,CS3;
SEC=Interrupt,F1A45,F1A54,F,CS3;
BANK=20,FFFF;
LOCATE=IRQVec,F1A4A;
```

The existing programmer's guide describes the memory regions. In this document, the relevant point is linker placement: `Flash` starts at the exact G1 entry. The linker therefore places its init table at `0x0E1A55` and C code immediately afterward.

The interrupt region is present because the Generalplus linker requires vector information in a body file. It does not mean those vectors should be copied into the embedded payload.

### Compile, assemble, link

The core commands used by `build.ps1` are conceptually:

```powershell
udocc.exe -S -O1 -Wall -mglobal-var-iram -mISA=2.0 `
  -DMOVIE_ADDR=... -DMOVIE_FRAMES=... `
  -o build\main.asm main.c

xasm16.exe -t4 -sr -wpop -o build\main.obj build\main.asm

xlink16.exe -as build\MaxFun.ary build\player.s37 `
  -initdata -body GPL16250VA_CS0SRAM -nobdy `
  -bfile MaxFunG1.bdy ...
```

The full command line also supplies the C macro library paths and the three undefined-option symbols expected by the library.

Treat warnings about undefined interrupt handlers differently from ordinary unresolved symbols. They are expected in this interrupt-disabled embedded handoff because the body must describe a vector area even though those records are excluded from the payload. Any other unresolved function is a build failure until explained.

### Always inspect the map

Do not trust a successful link alone. At minimum, verify:

- the init table starts at the donor entry;
- `_main` is inside the replacement window;
- all CODE and initialized-data sections are below the protected boundary;
- uninitialized globals have addresses that do not overlap appended assets;
- no unexpected library section is placed near the vector bank;
- the main address used by the startup GOTO matches the map.

In the final build, `_main` is located near `0x0E1B90`; the exact low words can change when C code changes, which is why the build script reads the map instead of hard-coding `_main`.

## Flattening S37 correctly

Motorola S37 records use byte addresses, while the linked unSP addresses are word addresses. The Generalplus output therefore represents word address `A` at S-record byte address `2*A`.

The flattener performs these operations:

1. Parse each `S3` record.
2. Read its 32-bit big-endian record address.
3. Reject any byte below `2 * player_base`.
4. Store bytes relative to `2 * player_base`.
5. Fill gaps with `0xFF`.
6. Round the result to an even byte count.

### Excluding the linker vector gap

The required interrupt region is one 64K-word bank above the player base. If the S37 file is flattened through those vector records, a tiny program becomes approximately 131,072 bytes before any assets are appended. That would consume almost the entire 149,518-byte safe window.

The working flattener takes a limit address and ignores records at or above:

```text
player_base + 0xFFF0 words
```

This keeps the real code and data while dropping the artificial vector tail. The startup executes `INT OFF`, so the omitted vectors cannot be entered by inherited firmware interrupts.

If a future application needs interrupts, this shortcut is not enough. That application must define a complete module-specific interrupt ownership plan, establish valid vectors, clear inherited sources, and prove the retail loader will not reclaim them. Refer to the existing programmer's guide for hardware interrupt behavior; the missing work is the MBA integration contract.

## The entry handoff

The first six payload bytes are patched after linking:

```text
40 F1    -> word 0xF140, INT OFF
8E FE    -> example GOTO A22 opcode for main in segment 0x0E
90 1B    -> example low 16 bits of _main
```

The exact GOTO words are generated from the linker map:

```python
goto_opcode = 0xFE80 | ((main_address >> 16) & 0x3F)
goto_low = main_address & 0xFFFF
```

### Why `INT OFF` is part of the file format contract

The retail loader calls the replacement while firmware devices and interrupt configuration still exist. Before interrupts were disabled, Bad Apple code ran and frames advanced, but the inherited video interrupt handler periodically restored pieces of the cyan `Loading` screen over the framebuffer. The captures contained thousands of non-black/non-white colors even though the player only wrote `0x0000` and `0xFFFF`.

With `INT OFF` at the first payload word:

- the indirect call to `0x0E1A55` still occurs;
- the GOTO reaches `_main`;
- the retail handler no longer rewrites display state;
- captures contain exactly two colors;
- consecutive captures have distinct hashes.

This is an integration rule, not a general recommendation that all MobiGo programs should avoid interrupts. A module that intentionally participates in the retail interrupt environment needs a more sophisticated handoff.

## Laying out code and assets

The payload has three regions:

```text
offset 0x0000              patched startup + linked player
offset player_size         zero padding
offset 0x2000              encoded movie stream
offset 0x2000+movie_size   end of payload
```

The movie begins at payload byte offset `0x2000`, which corresponds to `0x1000` unSP words. With the G1 player base:

```text
movie word address = 0x0E1A55 + 0x2000 / 2
                   = 0x0E2A55
```

The build uses two link passes:

1. Build once with a provisional asset address.
2. Flatten and measure the program.
3. Choose an aligned asset byte offset, at least `0x2000` here.
4. Convert the byte offset to words and calculate the final asset address.
5. Rebuild with `MOVIE_ADDR` set to that final address.
6. Flatten again, patch startup, pad, and append the asset.

The reserved gap is not wasted thoughtlessly. It ensures the linked code and uninitialized global address range do not collide with appended assets. A production script should derive the minimum from the map rather than relying only on a constant.

### Bad Apple asset format

The movie was reduced to 64 x 48 monochrome frames and displayed at 5x nearest-neighbor scale on the 320 x 240 screen. The source was encoded at 10 frames per second, with 500 frames in the payload.

Each logical frame contains:

```text
64 * 48 = 3,072 bits = 192 16-bit words
```

Compression is based on the XOR delta from the previous frame. The 192-word delta is split into zero and nonzero runs:

- token bit 15 clear: skip `token & 0x7FFF` unchanged words;
- token bit 15 set: consume that many literal XOR words immediately following the token;
- each frame begins with the encoded frame length in words, excluding the length word itself.

Decoder outline:

```c
end = src + *src + 1;
++src;
while (src < end) {
    token = *src++;
    count = token & 0x7fff;
    if (token & 0x8000) {
        while (count--)
            bitmap[pos++] ^= *src++;
    } else {
        pos += count;
    }
}
```

The encoded results in the final build are:

| Component | Size |
|---|---:|
| Flattened linked player | about 1.1 KiB |
| Reserved player/padding region | 8,192 bytes |
| 500-frame movie stream | 121,770 bytes |
| Final flat payload | 129,962 bytes |
| Safe G1 window | 149,518 bytes |
| Remaining margin | 19,556 bytes |

The format has no random access table; playback is sequential. Looping resets the source pointer and clears the delta bitmap.

### Far-pointer boundary defense

The Generalplus compiler uses multiword pointers for addresses above the low segment. Long sequential writes can cross a `0xFFFF` low-word boundary. The final renderer explicitly resets its framebuffer pointer at the known `0x1FFFF` to `0x20000` transition rather than depending solely on generated carry behavior.

This is defensive code that makes the intended address transition obvious in both emulator traces and generated assembly. For any large buffer:

- calculate every 64K-word boundary it crosses;
- inspect generated assembly around pointer increment;
- use explicit far-pointer helpers or boundary resets if behavior is uncertain;
- test the whole buffer, not just its first lines.

Hardware pointer semantics are covered by the existing programmer's guide. The MBA-specific lesson is that a correct package can still expose compiler ABI assumptions that a direct cartridge test did not reveal.

## Building the donor-backed MBA

The packer is intentionally small and conservative. Its job is not to reinterpret the whole file.

### Required inputs

- the exact stock G1 MBA extracted from the target firmware/NAND;
- the flat payload linked at the stock G1 entry;
- the expected G1 magic, entry, and boundary values;
- a separate output path.

### Validation before mutation

The packer checks:

1. Magic equals `bM_gbMQa`.
2. Declared words at `0x08`, multiplied by two, equal actual file bytes.
3. Entry at `0x14` maps to file offset `0x334AA` for this donor.
4. Payload end is no later than `0x57CB8`.
5. Output length remains exactly the donor length.
6. All bytes before the entry remain identical.

### Replacement algorithm

In concise form:

```python
stock = bytearray(stock_path.read_bytes())
payload = payload_path.read_bytes()

declared_bytes = u32le(stock, 0x08) * 2
entry = u32le(stock, 0x14)
protected = u32le(stock, 0x10)

entry_offset = (entry - 0x0C8000) * 2
safe_end = (protected - 0x0C8000) * 2

assert declared_bytes == len(stock)
assert entry_offset == 0x334AA
assert entry_offset + len(payload) <= safe_end

stock[entry_offset:entry_offset + len(payload)] = payload
output_path.write_bytes(stock)
```

Everything after the payload remains donor data. Loader references at and beyond the protected boundary remain intact.

### The G1 entry is an application launch routine, not a reset vector

Physical-hardware testing established the launch lifetime. Returning from the
G1 entry tells LD that the application exited, so LD is shown again. Stock
traces that alternate between G1 and system addresses are OS calls and
interrupt handlers within one running application; they do not prove that the
entry itself is being called once per frame.

A resident replacement must:

1. Stay in its application loop until it intentionally exits.
2. Preserve inherited IRQ/FIQ state; do not issue `INT OFF` at entry.
3. Service the inherited watchdog regularly.
4. Use bounded DMA waits and avoid conflicting with OS-owned DMA activity.
5. Keep hardware interrupts available for the retail display and system services.

The failed resident probe disabled IRQ and FIQ with opcode `0xF140`. Emulator2
continued presenting frames, but the physical unit remained white. A corrected
probe kept both interrupt-enable bits set and successfully displayed colors on
the real device. Use loop-local or deliberately allocated storage for animation
state; returning is the application-exit path.

### Why the file size is kept exact

An early probe appended a new page and increased G1 from `0x214000` to `0x215000` bytes. The retail path remained on `Loading`. The donor contains internal assumptions about allocation and/or section extents beyond the top-level size field. Merely updating the filesystem entry or header length is not enough.

The working approach therefore preserves:

- top-level declared word count;
- physical MBA byte length;
- header CRC;
- title and role;
- pre-entry loader bytes;
- protected callbacks/tables;
- tail resource extent.

Treat same-size substitution as a safety property, not an incidental convenience.

## Installing the MBA into MOBIGOFS

The existing programmer's guide explains NAND controller hardware. This section concerns the host-side filesystem editor, a separate layer not covered there.

The verified source NAND is:

```text
`/path/to/source-nand.bin`
```

The installation script writes a new image:

```text
`/path/to/nand.edited.bin`
```

The source file is hashed before and after the operation and must remain unchanged.

### Relevant MOBIGOFS structure

The editor translates raw NAND first, using the logical erase-block number stored in OOB bytes 2-3. Within the translated image it locates `MOBIGOFS3.0` snapshots.

The filesystem organization recovered by the editor is:

- filesystem block: `0x4000` bytes;
- half block: `0x2000` bytes;
- record: `0x200` bytes;
- record payload: 504 bytes, with four wrapper bytes on each side;
- useful payload per half: 8,064 bytes;
- file size stored in 16-bit words;
- second half of a file-index block is the first data extent;
- referenced data blocks contribute both halves.

Each 512-byte record ends with:

- bytes 508-509 mirroring the record's first two bytes;
- a 16-bit additive checksum over the first 255 little-endian words.

The installer does not search and overwrite raw MBA byte patterns. It walks the directory tree, finds the G1 MBA in every detected snapshot, follows its file index, writes payload records, updates sizes when necessary, refreshes record wrappers/checksums, converts the translated logical image back to raw NAND pages, and then reopens the result for a byte-for-byte file read-back.

### Installation command

```sh
cd emulator
python3 script.py BadAppleG1/BADAPPLE_135804G1.MBA
```

Expected success properties:

```text
PASS installed ... as /BUNDLE/G1/135804G1.MBA
PASS verified all filesystem snapshot entries
PASS source NAND unchanged
Wrote .../nand.edited.bin
SHA-256 ...
```

The general-purpose editor is:

```text
tools/mobigo2_nandfs_editor_v2.py
```

For same-size donor substitution, no new file allocation should be necessary. The expansion code exists for larger inputs, but a larger MBA has already been shown to violate the G1 donor's internal assumptions and should not be treated as a solution to payload overflow.

## Emulator verification through the retail path

The test must exercise the same menu path a user will take. Directly starting the payload or forcing the PC to its entry only proves that the code is executable; it does not prove the MBA is accepted, loaded, or called correctly.

### Deterministic touch sequence

For the verified US stitched NAND:

```text
Hamster Highway: at 350,000,000 instructions, hold 10,000,000, x=165, y=82
Easy:            at 680,000,000 instructions, hold 10,000,000, x=100, y=205
```

The second touch must wait for the carousel/selection transition. A much earlier Easy touch can occur while the menu is still moving and creates a false failure.

### Final acceptance command

```sh
cd emulator

./mobigo2_emu \
  --rom internalrom.bin \
  --spi spi.bin \
  --nand nand.edited.bin \
  --no-window \
  --steps 950000000 \
  --touch-event 350000000,10000000,165,82 \
  --touch-event 680000000,10000000,100,205 \
  --dump-frame-dir BadAppleG1/final-frames \
  --dump-frame-interval 5000000 \
  --dump-frame BadAppleG1/final-950m.bmp
```

The hardware options and frame-dump behavior are documented in the existing programmer's guide. The new MBA-specific requirement is the full navigation sequence before examining payload behavior.

### Trace proof

A focused trace observed:

```text
INDIRECT CALL ... target=0xe1a55
0e1a55: f140    ; INT OFF
0e1a56: fe8e    ; GOTO high/opcode
0e1a57: ....    ; GOTO low word
... _main ...
```

The exact `_main` low word changes with the build. The first target and `INT OFF` must remain stable for this donor.

### Frame proof

The final run captured frames at 885M, 915M, and 950M instructions. Each capture:

- contains exactly black and white pixels;
- has a different SHA-256 hash;
- visibly shows a different Bad Apple silhouette;
- contains no cyan `Loading` pixels.

Three different hashes alone would not be enough; corrupted noise also changes. The two-color invariant is a content-aware assertion derived from the player design.

The retained proof files are:

```text
representative frame captures from the local emulator test run
```

## Failure signatures and their causes

### The menu stays on Loading after MBA expansion

**Cause:** the donor was made larger by appending a page. Top-level file size alone did not describe every internal extent expected by the loader.

**Fix:** keep the exact donor size and fit the payload inside a verified existing window.

### The emulator crashes before the replacement entry

**Cause:** replacement began at the entry but extended through loader-referenced code or metadata around the `0x10` header reference.

**Fix:** cap the payload before file offset `0x57CB8` for this G1 donor.

### The entry jumps to an unknown opcode in a later address region

**Cause:** a later MBA resource offset was assumed to map linearly. The loader transformed that section, so runtime memory contained image/resource data instead of the linked player.

**Fix:** execute entirely from the verified linear code region, or reverse-engineer the specific resource descriptor before using it.

### Code runs when started directly but fails as G1

**Cause:** direct binary was linked at `0x50000`, while the retail loader called `0x0E1A55`. Absolute calls, globals, and asset pointers still referred to the old address family.

**Fix:** relink the entire program at the donor entry. Patching only the first jump cannot relocate all absolute references.

### Frame zero appears but never advances

**Cause:** the player polled a PPU status bit whose generation depended on display/interrupt setup not active at the module handoff.

**Fix:** use a self-contained timing source during bring-up. Integrate a hardware timer or video edge only after proving its state under retail module launch. Refer to the existing guide for timer/video details.

### Bad Apple is visible but Loading text reappears

**Cause:** inherited retail video interrupts remained enabled and rewrote framebuffer/display state.

**Fix:** execute `INT OFF` before entering C, or deliberately take ownership of every inherited interrupt source and vector.

### Player binary is approximately 131,072 bytes before assets

**Cause:** the S37 flattener included linker-required vector records one 64K-word bank above the program.

**Fix:** exclude vector-tail records for an interrupt-disabled embedded module.

### Movie pointers are off by a factor of two

**Cause:** payload offsets are bytes, while C/linker runtime addresses are unSP words.

**Fix:** add `payload_byte_offset / 2` to the runtime word base.

### Header looks right but the wrong menu role launches

**Cause:** MBA role is not defined by extension or magic alone. The retail menu expects slot-specific metadata and behavior.

**Fix:** use a donor from the same exact slot and firmware family, retain its title and unknown header fields, and test through the actual menu.

## A reusable project workflow

The following sequence is recommended for a new G1 experiment.

### Phase 1: freeze the donor

1. Extract G1 from the exact NAND/firmware being tested.
2. Record its SHA-256, byte length, magic, title, declared word count, header CRC, entry, load base, and protected callback/reference.
3. Keep an immutable copy.
4. Compare its header against known retail G1 samples.

### Phase 2: define the payload budget

1. Derive `entry_offset` from the verified mapping.
2. Derive the conservative protected offset.
3. Calculate available bytes.
4. Reserve margin rather than filling the window exactly.
5. Design asset quality around the budget before writing a large engine.

### Phase 3: write freestanding application code

1. Avoid assumptions about reset state; this is a called module.
2. Decide whether to disable or own inherited interrupts.
3. Avoid dynamic runtime dependencies until the link map is understood.
4. Keep large assets outside object-file padding and append them explicitly.
5. Make content invariants testable: fixed palette, frame counter, signature pixels, or hashes.

For hardware API usage, refer to the existing programmer's guide instead of duplicating register setup here.

### Phase 4: link at the donor entry

1. Set the body `Flash` origin to the entry word address.
2. Compile and assemble.
3. Link to S37.
4. Inspect the map.
5. Flatten relative to the same origin.
6. Exclude artificial vector padding only when interrupts are disabled.
7. Preserve IRQ/FIQ and enter a watchdog-serviced application loop.

### Phase 5: build assets with a two-pass address

1. Encode assets.
2. Measure the flattened player.
3. Choose a padded byte offset above all linked storage.
4. Convert the offset to words.
5. Rebuild with the final runtime asset address.
6. Assert the combined payload fits.

### Phase 6: package conservatively

1. Revalidate donor fields.
2. Copy the donor to a new byte array.
3. Replace only the allowed window.
4. Keep the original file length.
5. Verify untouched prefix and protected suffix.
6. Parse the output header again.
7. Record SHA-256.

### Phase 7: install and read back

1. Start from a known NAND hash.
2. Replace G1 through MOBIGOFS structures.
3. Write a separate `nand.edited.bin`.
4. Reopen the new raw NAND.
5. Read G1 through the filesystem parser.
6. Require exact equality with the built MBA.

### Phase 8: test the retail path

1. Boot retail ROM/SPI/NAND.
2. Inject the Hamster Highway touch.
3. Wait for the carousel.
4. Inject Easy.
5. Trace the indirect call to the donor entry.
6. Verify the app remains resident without returning to LD.
7. Verify IRQ/FIQ stay enabled and the watchdog does not reset the unit.
8. Capture a sequence, not only a final frame.
9. Assert application-specific invariants and frame changes.
10. Save the exact tested MBA and its checksum.

## Generalizing beyond G1

Do not copy `0x0C8000`, `0x0E1A55`, `0x334AA`, or `0x57CB8` into another slot packer.

For a new donor:

1. Parse its header and compare it with multiple real samples.
2. Observe the retail loader's actual indirect call target.
3. Dump runtime memory before entry.
4. Search for exact file-to-memory correlations.
5. Establish where linear mapping begins and ends.
6. Patch only a minimal instruction first, without changing file size.
7. Confirm the patched instruction is fetched.
8. Expand the replacement gradually while monitoring pre-entry behavior.
9. Identify every header pointer/reference whose target must survive.
10. Treat resource sections as non-linear until proved otherwise.

Main-menu (`MM.MBA`) is especially different: its real sample uses a `0x224800` load family and an entry at `0x22D8A5`. A G1-derived formula cannot be transferred to it by changing only the title.

## Real hardware preparation

The final artifact is emulator-verified and retail-format-derived, but hardware deployment adds risks that an emulator cannot eliminate.

Before writing a device:

- make a complete verified NAND backup, including OOB/spare bytes;
- extract and hash the device's original G1 MBA;
- confirm its header and size match the donor used for packaging;
- preserve the original filename in `/BUNDLE/G1`;
- prefer a filesystem-aware replacement path over arbitrary raw page writes;
- read the installed file back from the device and compare every byte;
- have a recovery/programmer path ready before the first boot;
- expect timing, watchdog, cache, and display behavior to differ from the emulator;
- test a short, easily recognized payload before a long animation.

If the device's G1 differs materially, rebuild against that donor. Do not force the tested MBA into a mismatched firmware simply because the filename is similar.

## What remains unknown for a true from-scratch MBA builder

A universal MBA generator would need more than the successful donor patch. Remaining work includes:

- identifying the complete header field semantics;
- locating and decoding every section/chunk descriptor;
- determining compression and relocation rules;
- identifying imports or callbacks supplied by retail firmware;
- understanding why some later resources are transformed to unrelated runtime addresses;
- determining whether other MBA families use content checks beyond the header CRC;
- characterizing role selection across regions and firmware revisions;
- defining how new file sizes propagate through every internal table;
- proving a generated MBA on physical hardware.

Until those are solved, donor-based same-size substitution is the better engineering description and the safer workflow.

## Reproducibility record for the working Bad Apple MBA

Final tested MBA:

```text
the locally built Bad Apple G1 MBA
```

Properties:

```text
bytes:       2,179,072 (0x214000)
magic:       bM_gbMQa
title:       MGB_G1
entry:       0x0E1A55
load field:  0x0C8800
header CRC:  0xA4D3
SHA-256:     bb7fe85849aae4c23cb56b55bacc0ae5783f97eac77602b33f5d832ccab9ac98
```

Final payload:

```text
runtime base:       0x0E1A55 words
MBA file offset:    0x334AA bytes
asset address:      0x0E2A55 words
payload bytes:      129,962
protected boundary: 0x57CB8 bytes
startup:            INT OFF; GOTO _main
movie:              500 frames, 64x48 1bpp, XOR/run encoded
display:            5x nearest-neighbor to 320x240
```

Final verification:

```text
navigation: Hamster Highway -> Easy
entry call: 0x0E1A55 observed
run length: 950,000,000 instructions
result: clean changing two-color frames
source NAND: unchanged
edited NAND: filesystem read-back exact
```

## Source and tool references

Primary references used for this document:

- Existing hardware guide: `docs/archive/mobigo2_programmers_guide.pdf`
- Retail MBA samples: user-supplied files from an authorized device backup
- MBA inspection tool: `tools/inspect_mba.py`
- Generalplus C projects: `examples/`
- MBA packer: `tools/pack_g1_mba.py`
- NAND installer: `tools/replace_g1_in_nand.py`
- MOBIGOFS editor: `tools/mobigo2_nandfs_editor_v2.py`
- Emulator source and CLI: `emulator/`

## Final checklist

Before calling an MBA build complete, require every box below:

- [ ] Exact-slot retail donor retained.
- [ ] Donor SHA-256 recorded.
- [ ] Header magic, declared size, actual size, title, entry, and CRC verified.
- [ ] Runtime/file mapping proved from memory, not guessed.
- [ ] Payload linked at the real retail entry.
- [ ] Link map inspected.
- [ ] Startup interrupt policy explicit.
- [ ] Asset byte offsets converted to word addresses.
- [ ] Payload ends before every protected loader reference.
- [ ] MBA length unchanged.
- [ ] Untouched donor regions compared byte-for-byte.
- [ ] NAND output written separately from source.
- [ ] Installed MBA read back through MOBIGOFS and compared exactly.
- [ ] Retail menu navigation automated.
- [ ] Indirect call to entry observed.
- [ ] Multiple frames captured.
- [ ] Content-aware frame assertions passed.
- [ ] Exact tested MBA and SHA-256 delivered together.

When all of these pass, the result is more than a binary that happens to execute. It is a reproducible, slot-compatible MBA build for the verified firmware path.
