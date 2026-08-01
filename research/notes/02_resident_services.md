# Resident service boundary

This document describes the fixed service bank called by official MobiGo
applications. Names beginning with `resident_` are clean-room working names;
they are not claimed to be official VTech or Generalplus symbols.

## Architectural result

Official MBA/GAM bodies contain substantial statically linked runtime code,
but they repeatedly call code outside their own mappings at word addresses
around `0x075c00..0x075fff`. This fixed bank is the clearest application/OS
boundary found so far:

```text
game code
  -> statically linked common runtime
       -> direct far CALL to 0x075xxx
            -> resident firmware service
```

The application images have no conventional import table. A compatible
homebrew SDK therefore needs declarations or wrappers for fixed resident
entry points rather than a dynamic linker.

## Runtime trampoline table

The existing emulator was used to boot the stock firmware for 100 million
instructions and capture word memory `0x050000..0x075fff`. The launcher footer
already identifies `0x075c00..0x075fe0`; the captured range proves that this
is a dense trampoline table:

- 496 two-word entries;
- every entry is a valid u'nSP far `GOTO`;
- 285 entries dispatch to implementations in `0x055dec..0x06d579`;
- 211 unsupported slots deliberately jump to themselves.

Selected resolved targets:

| Service | Implementation | Working meaning |
|---:|---:|---|
| `0x075e06` | `0x05ef19` | register title audio root and optional patch root |
| `0x075e0a` | `0x05f1e6` | apply master volume |
| `0x075e0e` | `0x05f3f8` | play sound |
| `0x075e1a` | `0x05f90f` | query sound state |
| `0x075e2c` | `0x05fb41` | play M music |
| `0x075e32` | `0x05fd4a` | pause music |
| `0x075e34` | `0x05fd61` | resume music |
| `0x075e36` | `0x05fd78` | stop music |
| `0x075e38` | `0x05fde0` | query music state |
| `0x075e3c` | `0x05fe1b` | set music repeat |
| `0x075e3e` | `0x05fe38` | get music level |
| `0x075e40` | `0x05fe53` | set music level |
| `0x075e5e` | `0x05c7ba` | request power-off |
| `0x075e60` | `0x065c29` | get current system-key mask |
| `0x075e62` | `0x065c32` | test system key down |
| `0x075e64` | `0x065c43` | test system-key pressed edge |
| `0x075e66` | `0x065c5b` | test system-key released edge |
| `0x075e8a` | `0x068a09` | post framework event |
| `0x075eaa` | `0x05d254` | get logical volume |
| `0x075eac` | `0x05d260` | set logical volume |
| `0x075eb2` | `0x05d28c` | get logical brightness |
| `0x075eb4` | `0x05d292` | set logical brightness |
| `0x075ec6` | `0x06d455` | get current game-control mask |
| `0x075ec8` | `0x06d45e` | test game-control down |
| `0x075eca` | `0x06d46f` | test game-control pressed edge |
| `0x075ecc` | `0x06d487` | test game-control released edge |
| `0x075ee0` | `0x06c75f` | get buffered input-code pointer |
| `0x075ee2` | `0x06c768` | get buffered input-code count |
| `0x075f12` | `0x056c54` | create UI object |
| `0x075f18` | `0x056e7c` | get UI object storage |
| `0x075f2e` | `0x0692fa` | get ticks |
| `0x075f3a` | `0x06cbd1` | get touch queue pointer |
| `0x075f3c` | `0x06cbda` | get touch queue count |
| `0x075f82` | `0x065d29` | apply backlight |
| `0x075fb4` | `0x06aac8` | test application path |
| `0x075fca` | `0x05aaf7` | schedule MBA launch |

The runtime capture and temporary decompiler listings remain outside this
clean-room tree. `research/reports/resident-service-targets.json` preserves only the
address map, counts, names, and input hash. The reproducible analysis tools
are `tools/re/decode_resident_trampolines.py` and the scripts under
`tools/ghidra`.

## u'nSP call encoding

The observed direct far-call instruction occupies two 16-bit words:

```text
word0 & 0xffc0 == 0xf040
target = ((word0 & 0x003f) << 16) | word1
```

Calls into the current service range use segment value 7, so a call to
`0x075eaa` is encoded with first word `0xf047` and second word `0x5eaa`.

`experiments/resident_abi_probe.c` checks this independently with the bundled
Generalplus compiler. Given:

```c
typedef unsigned short u16;
typedef u16 (*service_get_u16)(void);

return ((service_get_u16)0x00075eaaUL)();
```

the compiler emits:

```text
R3 = 0x5eaa
R4 = 7
call MR
```

For a one-word argument, the compiler places the argument in an outgoing
stack slot before the same `call MR`. This proves that ordinary C function
pointers can generate the required far transfer with the SDK's 32-bit pointer
model. It does not, by itself, prove every reconstructed prototype or service
meaning.

## Cross-image call census

`tools/re/catalog_resident_calls.py` scans all MBA/GAM bodies for direct far-call
encodings in `0x075c00..0x075fff`. The current report covers 14 images.
Because executable bodies also contain data, every raw opcode hit is a
candidate until its containing function is checked in Ghidra. Repetition at
the same even service address across independently linked applications is
strong supporting evidence.

Selected results:

| Target | Images | Raw calls | Current interpretation |
|---:|---:|---:|---|
| `0x075e0a` | 6/14 | 20 | apply mapped master volume |
| `0x075e0e` | 7/14 | 34 | start sound playback |
| `0x075e1a` | 7/14 | 16 | query sound state |
| `0x075e5e` | 8/14 | 11 | request power-off |
| `0x075e64` | 7/14 | 33 | test a system-key pressed edge |
| `0x075e7c` | 6/14 | 30 | create opaque context |
| `0x075e7e` | 6/14 | 29 | destroy opaque context |
| `0x075e82` | 6/14 | 56 | get context storage pointer |
| `0x075e84` | 6/14 | 63 | release context storage |
| `0x075eaa` | 6/14 | 6 | get logical volume |
| `0x075eac` | 6/14 | 11 | set logical volume |
| `0x075eb2` | 6/14 | 15 | get logical brightness |
| `0x075eb4` | 6/14 | 6 | set logical brightness |
| `0x075f12` | 7/14 | 26 | create resident family-B UI object |
| `0x075f18` | 8/14 | 462 | get resident family-B UI-object storage |
| `0x075f2e` | 6/14 | 188 | obtain resident tick count |
| `0x075f46` | 8/14 | 8 | application-entry setup step |
| `0x075f48` | 8/14 | 8 | application-entry dispatch step |
| `0x075f4a` | 8/14 | 8 | application-entry finalization |
| `0x075f52` | 8/14 | 8 | GPIO-B-bit-9 hardware sequence; peripheral unresolved |
| `0x075f82` | 6/14 | 18 | apply mapped backlight value |
| `0x075fb4` | 7/14 | 31 | test application path |
| `0x075fca` | 6/14 | 28 | launch another MBA |
| `0x075fcc` | 6/14 | 15 | query launch volume/path state |

The `0x075f46`, `0x075f48`, and `0x075f4a` cluster is the shared application
setup/step/finalize contract. Live resident decompilation corrected the older
interpretation of `0x075f52`: it toggles GPIO-B bit 9 around a short hardware
service and is not the application initializer. The high counts at `0x075f18`
and `0x075f2e` are consistent with per-frame object access and timing.

## Reconstructed interfaces

The first target-side adapter is `src/resident_backend.c`. It connects the
portable system-controls policy to
these strongly supported resident entries:

```c
int resident_system_key_pressed(unsigned short mask);
unsigned short resident_get_volume_level(void);
void resident_set_volume_level(unsigned short level);
void resident_apply_master_volume(unsigned short gain);
unsigned short resident_get_brightness_level(void);
void resident_set_brightness_level(unsigned short level);
void resident_apply_backlight_level(unsigned short value);
unsigned long resident_get_ticks(void);
void resident_request_poweroff(void);
```

These declarations show the current effective types; actual code uses
private function-pointer typedefs and fixed addresses so it does not imply
that symbol names exist on the device.

The adapter compiles and assembles with the Generalplus toolchain used by the
integrated starter project.
Resident UI, sound, music, input, storage, text, and lifecycle paths have now
been invoked by clean-room MBAs in the emulator. Physical-hardware validation
is still pending, and uncommon service side effects remain conservative where
no title or runtime test exercises them. The captured resident image is kept in
the persistent headless Ghidra project `build/ghidra-resident/ResidentRuntime`.

Overlay and feedback-sound callbacks remain deliberately absent from the
generic target adapter so homebrew can supply original presentation and
sounds. The lower linked-bundle registration and UI family-A/family-B
services are now exposed separately through
`include/mobigo_sdk/resident_resources.h`; their recovered container and
graphics layouts are documented in `research/notes/09_asset_bundle_runtime.md`.
Application path testing and the three-argument MBA launch request are
exposed through `include/mobigo_sdk/application.h`.

## Cross-title verification status

SY, G2, G3, and G4 have now been analyzed headlessly in addition to the
connected G1 program. SY confirms the full runtime lifecycle and input/UI
semantics. G2/G3/G4 confirm that linked settings tables and their mode
constants are generated together and may be compacted per title.
