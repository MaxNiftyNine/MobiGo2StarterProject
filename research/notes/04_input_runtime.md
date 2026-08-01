# Common input event runtime

G1's function at `0x0dd3cc`, now named
`sdk_input_and_system_controls_poll`, is the shared per-frame input pump as
well as the volume/brightness overlay manager. It translates several
resident input sources into framework event `0x1005`.

Names in this document are clean-room working names.

## Framework event

Local G1 helper `sdk_post_input_event` at `0x0dd19e` invokes resident service
`0x075e8a` with:

```text
event ID = 0x1005
fixed routing fields = -1, -1, -2, -1
payload = code, kind, x, y
```

It then records the 32-bit tick count from `0x075f2e`, making the timestamp
available to inactivity and overlay logic.

The observed input kinds are:

| Kind | Source | Code |
|---:|---|---|
| 2 | buffered or special keyboard input | one-byte keyboard code |
| 3 | game controls | named bit from Up/Down/Left/Right/Primary/Exit/Help |
| 4 | system key | Off mask `0x0200` |

G1 supplies `x = -1`, `y = -1` for all of these. The presence of coordinate
fields suggests that the wider event structure may support pointer input, but
this function does not establish the touch path.

## Resident input services

Direct decompilation of the resident implementations establishes:

| Service | Implementation | Current behavior |
|---:|---:|---|
| `0x075e60` | `0x065c29` | Returns the current system-key mask |
| `0x075e62` | `0x065c32` | Tests whether a system-key bit is currently down |
| `0x075e64` | `0x065c43` | Tests a system-key pressed edge: `current & changed & mask` |
| `0x075e66` | `0x065c5b` | Tests a system-key released edge: `~current & changed & mask` |
| `0x075ec6` | `0x06d455` | Returns the current game-control mask |
| `0x075ec8` | `0x06d45e` | Tests whether a game-control bit is currently down |
| `0x075eca` | `0x06d46f` | Tests a game-control pressed edge |
| `0x075ecc` | `0x06d487` | Tests a game-control released edge |
| `0x075ee0` | `0x06c75f` | Returns a far pointer to the first buffered input-code entry |
| `0x075ee2` | `0x06c768` | Returns the buffered input-code count |
| `0x075ee6` | `0x06c783` | Delegates a special-key-code test to lower resident service `0x006fb4` |
| `0x075e8a` | `0x068a09` | Constructs and submits a nine-word framework event |

The system update routine at `0x0657c7` and game update routine at `0x06d397`
both use the exact state transition:

```c
changed = old_current ^ new_current;
current = new_current;
```

Therefore `0x075e64` and `0x075eca` are unambiguously one-frame pressed-edge
tests, not held/debounced tests. Their matching release tests are
`0x075e66` and `0x075ecc`. The clean-room runtime now exposes all three
query forms directly: current/down, pressed edge, and released edge.

## Physical-to-logical key maps

The low-RAM calls made by the resident update routines are themselves
two-word trampolines. A live retail-firmware code dump resolves:

| Low service | Implementation | Mapping table |
|---:|---:|---:|
| `0x006fac` | `0x03059a` | game controls at `0x03cb3b` |
| `0x006fae` | `0x0305f0` | system controls at `0x03ccd0` |

Each implementation walks terminated three-word records:

```c
struct resident_physical_key_map {
    uint16_t logical_mask;
    uint16_t scanned_row_word;
    uint16_t physical_mask_index;
};
```

It tests the indexed physical mask against one scanned row word and ORs
`logical_mask` into the result. Correlating those records with the independently
verified GPIO matrix gives:

| Logical mask | Control | Matrix cell |
|---:|---|---|
| `0x0001` | Up | R3 C4 |
| `0x0002` | Down | R4 C4 |
| `0x0004` | Left | R3 C3 |
| `0x0008` | Right | R4 C3 |
| `0x0010` | Primary | R3 C5 |
| `0x0020` | Exit | R4 C2 |
| `0x0040` | Help | R4 C5 |
| `0x0200` | Off | R3 C2 |
| `0x0400` | Volume up | R4 C8 |
| `0x0800` | Volume down | R4 C7 |
| `0x1000` | Brightness | R4 C6 |

The scan buffer packs physical columns C6, C7, and C8 into masks `0x20`,
`0x40`, and `0x80`; it is not a direct copy of the original GPIO bit
positions. The named system masks above are also independently confirmed by
G1's volume and brightness handlers.

The live matrix scanner at `0x03a0e0` packs each active row as:

```c
row_bits = (GPIO_B & 0xfc00) | ((GPIO_A & 0x3800) >> 6);
```

For row 4 / Brightness, GPIO-A bit `0x0800` therefore becomes scan-buffer mask
`0x0020`. The live system map associates row 4 / physical-mask index 0
(`0x0020`) with logical mask `0x1000`.

This complete path is now runtime-verified in a clean replacement MBA. A
post-launch scripted Volume+ edge advances the template level from 7 to 8, and
a held Brightness key advances brightness from 2 to 3 exactly once while
recording logical mask `0x1000`. `make homebrew-check` rebuilds and repeats the
experiment.

## Per-frame sequence

G1 performs these steps:

1. If buffered input count is positive, post the low byte of the first entry
   as kind 2.
2. Test special codes `0x90` and `0x14`; post a kind-2 transition when each
   becomes active.
3. Test game controls in order Left, Right, Up, Down, Primary, Exit, Help;
   post each active one as kind 3.
4. Test system mask `0x0200` and post it as kind 4.
5. Run the volume, brightness, Off-sequence, and transient-overlay policy.

A second G1 routine at `0x0dfa5c` iterates all buffered codes and translates
them through a 74-entry table. It separately tracks two special states and
uses codes `0x14` and `0x90`, confirming this family is keyboard/code input,
not the touchscreen queue.

Touch input is not handled by this particular framework-event pump. The
separate touch queue and its G1 dispatcher are documented in
`06_ui_touch_runtime.md`.
