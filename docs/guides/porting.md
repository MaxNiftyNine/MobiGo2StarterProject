# Port an existing game

Treat a port as an adaptation to a resident application platform, not as a
desktop executable cross-compile. This checklist is suitable for a human
developer or a coding agent receiving a request such as “port Doom to MobiGo 2.”

## 1. Write the port contract first

Record these decisions before editing upstream code:

| Question | Canonical answer for a new port |
| --- | --- |
| Target profile | SY |
| Runtime model | resident setup/step/finalize |
| System controls | `standard_controls.h`; `direct_controls.h` only for a direct loop |
| Game input | resident logical keys; keyboard alternatives where useful |
| Rendering | resident resources, or inherited framebuffer through `hardware.h` for a software renderer |
| Bulk copies | SDK DMA helpers when worthwhile |
| Mutable state | explicit application-owned title RAM |
| Assets | `const` linked data generated reproducibly |
| Testing | host/target suite plus a deterministic emulator smoke test |
| Target language | C99-style C; optional u'nSP `.asm`/`.s`; no target C++ ABI |

State any exception and why it is necessary. Do not choose G1 merely because an
older complete example does.

## 2. Audit feasibility

Measure rather than guess:

- linked code and immutable asset size versus the selected profile capacity;
- worst-case writable memory, stack, framebuffers, audio buffers, and resource
  graphs;
- integer-width assumptions, alignment, endianness, and pointer casts;
- dependencies on files, threads, floating point, a standard library, dynamic
  allocation, operating-system timing, or signals;
- C++ source, constructors/destructors, exceptions, RTTI, templates, or a C++
  standard library that must be translated/isolated because the target builder
  is C plus assembly today;
- framebuffer dimensions and conversion cost;
- source and license compatibility.

The CPU addresses 16-bit words. File formats still use bytes. Any upstream code
that serializes pointers, assumes byte-addressed target pointers, or uses fixed
32-bit host types deserves special review.

## 3. Isolate the portable game core

Keep upstream simulation separate from platform operations. A small frontend
should own:

- startup and explicit state initialization;
- input translation;
- video conversion/presentation;
- audio submission;
- storage paths;
- resident callbacks and standard controls.

Avoid spreading MobiGo addresses through upstream gameplay files. If low-level
access is needed, contain it behind `hardware.h` or one platform module.

## 4. Adapt lifecycle and memory

There is no ordinary initialized-data startup at the direct MBA entry. Convert
writable initialized globals into one of:

- immutable `const` templates copied into owned RAM;
- explicit assignments during application start;
- a state block whose entire contents are deliberately initialized.

Keep the resident frame callback bounded. It should advance input, system
controls, game simulation, rendering, and audio, then return. A tight inner game
loop prevents resident services and scheduled handoffs from progressing.

## 5. Choose the graphics path

Use resident resources for object-oriented UI, sprites, animation, and text.
Use the inherited framebuffer helpers for an existing software renderer.

For a framebuffer port:

1. obtain the launcher-selected buffer rather than assuming an SDRAM address;
2. choose a compact internal format when the original resolution is small;
3. convert or scale into the 320×240 display with bounded work;
4. use system DMA for large fills or copies;
5. preserve inherited interrupts and service the watchdog;
6. test clipping, stride, color conversion, and buffer presentation.

Do not copy raw MMIO snippets from archived G1 experiments.

## 6. Map every input deliberately

Document a table of game actions, physical controls, keyboard alternatives, and
scripted emulator names. Keep system buttons available to the standard-control
layer.

For example, an action may accept both a large D-pad direction and a letter key,
but those are distinct matrix cells. Test each alternative, pressed edges,
holds, and simultaneous directions.

## 7. Integrate platform behavior

Poll `mg_sdk_standard_controls_poll()` once per resident frame. Do not merely
draw a volume or brightness overlay: the standard layer also owns setting
application, persistence, timeouts, and the Off sequence.

If the port deliberately owns a direct framebuffer loop and does not step
resident rendering, use `mg_sdk_direct_controls_poll()` instead. It scans raw
matrix edges and preserves setting application, persistence, and power-off,
but draws no overlay because resident UI is inactive.

Add audio and storage only after the basic frame/input path is stable. Bound all
storage operations and use packed resident paths through the SDK.

## 8. Build reproducibly

Make all source and asset inputs explicit. Asset generation must be deterministic
and run from a clean checkout. Do not append blobs after linking, patch addresses
from a previous binary, copy a private linker body, or depend on a donor MBA.

The routine commands should remain:

```sh
python3 tools/mobigo.py build
python3 tools/mobigo.py run
python3 tools/mobigo.py test
```

## 9. Add a deterministic emulator regression

A useful smoke test boots through the role-aware transient overlay, injects inputs, and checks an
observable result such as a frame region, memory signature, audio state, or
scene transition. It should cover:

- boot to the first interactive frame;
- start/confirm input;
- representative movement or action;
- standard controls;
- a stable progress marker after several frames;
- clean failure output when the marker is absent.

Large games need more than a launch screenshot. Test at least one full gameplay
transition and any custom renderer or audio path.

## 10. Separate claims by evidence

Report compilation, emulator behavior, and physical behavior separately. A
working emulator port is valuable, but it is not automatically physical-device
confirmation. Record remaining gaps in the capability matrix or the project's
own README rather than hiding them.

## Port handoff checklist

- [ ] SY retained or G1 exception documented
- [ ] no hard-coded regional filename
- [ ] no initialized writable-global dependency
- [ ] standard controls integrated
- [ ] every game action has tested mappings
- [ ] renderer uses resident APIs or documented `hardware.h` helpers
- [ ] watchdog and inherited display ownership respected
- [ ] assets are reproducible and licensed
- [ ] host and target checks pass
- [ ] role-aware emulator smoke test passes
- [ ] copied-NAND parity passes when packaging/storage/install behavior changed
- [ ] physical status stated honestly
