# Common system controls and lifecycle layer

This document describes the clean-room working model of the MobiGo 2 runtime
code responsible for volume, brightness, the Off button, transient status UI,
and application handoff. Names beginning with `sdk_` or `resident_` are
descriptive names assigned during this research; they are not claimed to be
VTech or Generalplus symbols.

## Result

The repeated controls are not merely similar game implementations. Full
applications statically link a common runtime layer that:

1. reads saved volume and brightness through fixed resident services;
2. applies logical settings through fixed resident services and lookup tables;
3. polls dedicated system-key bits independently of ordinary game input;
4. displays a shared transient UI object;
5. plays common feedback sounds;
6. handles Off-button presentation and requests system power-off;
7. hands control to SY, MM, UB, or another application when necessary.

LD and TM are small role-specific applications and omit the full layer.

## G1 control flow

```text
sdk_runtime_init (0x0e0000)
  |
  +-- sdk_system_controls_init (0x0dd1fc)
  |     +-- load and apply volume
  |     +-- load and apply brightness
  |     `-- create status UI object type 0x0e
  |
sdk_runtime_tick_and_handoff (0x0e0075)
  |
  +-- sdk_update_poweroff_sequence (0x0e0211)
  +-- sdk_input_and_system_controls_poll (0x0dd3cc)
  |     +-- sdk_handle_volume_keys (0x0dd715)
  |     `-- sdk_handle_brightness_key (0x0dd984)
  |
  `-- launch SY/MM/UB or another MBA when the application exits
```

Addresses are G1 word addresses.

## Logical settings

### Volume

The runtime stores a logical volume from 0 through 9. An invalid saved value
is replaced with 7. The logical value is converted through:

```text
logical:       0   1   2   3   4   5   6   7   8    9
resident gain: 4  14  25  35  45  55  67  79  91  105
```

The gain table is at G1 `0x0e2106`. The runtime:

- treats resident key mask `0x0400` as volume up;
- treats resident key mask `0x0800` as volume down;
- saturates rather than wrapping at 0 and 9;
- uses feedback sound `0x20e4`, except that the maximum-level case uses
  `0x20e5`;
- applies the mapped gain through resident service `0x075e0a`;
- persists the logical level through `0x075eac`;
- selects status-UI mode 4 with the logical level as its index;
- places the UI object at `(109, 214)`;
- records the display time and hides the object after `0x13f1` resident
  ticks.

### Brightness

The runtime stores a logical brightness from 0 through 3. An invalid saved
value is replaced with 2. The hardware mapping is:

```text
logical:          0  1   2   3
backlight value:  1  5  10  15
```

The table is at G1 `0x0e2112`. The runtime:

- treats resident key mask `0x1000` as brightness;
- increments and wraps across four levels;
- persists the logical level through `0x075eb4`;
- applies the mapped value through `0x075f82`;
- selects status-UI mode 1 with the logical level as its index;
- places the UI object at `(138, 214)`;
- plays feedback sound `0x20e4`;
- uses the same transient-display timer as volume.

### Off button

`sdk_update_poweroff_sequence` polls resident system-key mask `0x0200`.
Depending on runtime state, it can create UI object type `0x30` at the screen
center `(160, 120)`, then begins the shutdown sequence:

1. stop or quiesce current audio/UI work;
2. notify the framework with event `0x1009`;
3. play sound `0x20de`;
4. poll the sound until it is no longer in the active state;
5. call resident service `0x075e5e`.

The final service is assigned working name `resident_request_poweroff`.
Confirming its implementation requires the resident firmware/service module,
but it has no other G1 call sites and appears only at the terminal point of
this sequence.

## Transient UI object

The controls state holds a handle created by resident service `0x075f12` with
object type `0x0e`. Service `0x075f18` returns a mutable object containing at
least these observed word fields:

| Field | Observed role |
|---:|---|
| `+0` | visible/active |
| `+1` | X position |
| `+2` | Y position |
| `+5` | display mode (`1` brightness, `4` volume) |
| `+6` | logical level/index |

The type-`0x30` centered object used by the Off sequence has additional
fields but is managed through the same resident object interface.

G1 registers a linked asset-bundle header at `0x0e2160` during runtime
initialization. The resident service relocates its tables and nested pointers
in place. The common settings object is now identified as a 12-word family-B
descriptor with five presentation modes: mode 1 contains four brightness
records and mode 4 contains ten volume records. See
`research/notes/09_asset_bundle_runtime.md` for the recovered layout. Clean-room
homebrew should use original status artwork rather than copying retail
resources.

## Resident service table

These meanings are inferred from the surrounding common-runtime code and
need confirmation against the resident service implementation:

| Address | Working name | Evidence |
|---:|---|---|
| `0x075e0a` | `resident_apply_master_volume` | Receives only values from the ten-step gain table |
| `0x075e0e` | `resident_play_sound` | Returns a handle; callers later query playback state |
| `0x075e1a` | `resident_get_sound_state` | Writes states including active value 2 |
| `0x075e5e` | `resident_request_poweroff` | Terminal call after Off sound completes |
| `0x075e64` | `resident_system_key_pressed` | Queried with masks `0x0200..0x1000` |
| `0x075e7c` | `resident_create_context` | Creates opaque context handle |
| `0x075e7e` | `resident_destroy_context` | Paired context teardown |
| `0x075e82` | `resident_get_context_pointer` | Converts handle to far pointer |
| `0x075e84` | `resident_release_context_storage` | Paired before context destruction |
| `0x075eaa` | `resident_get_volume_level` | Result is validated against 0..9 |
| `0x075eac` | `resident_set_volume_level` | Receives the updated logical volume |
| `0x075eb2` | `resident_get_brightness_level` | Result is validated against 0..3 |
| `0x075eb4` | `resident_set_brightness_level` | Receives the updated logical brightness |
| `0x075f12` | `resident_create_ui_object` | Returns an opaque two-word handle |
| `0x075f18` | `resident_get_ui_object` | Returns mutable UI-object storage |
| `0x075f2e` | `resident_get_ticks` | Repeated 32-bit time-difference calculations |
| `0x075f82` | `resident_apply_backlight_level` | Receives only mapped backlight values |

### Resident implementation confirmation

The runtime resident-module capture resolves and decompiles the underlying
implementations:

- `0x075eaa -> 0x05d254 -> 0x061062(0)` returns the low nibble of persistent
  settings word `0x014c`, or `0xffff` when settings are unavailable.
- `0x075eac -> 0x05d260 -> 0x060f63(0, level)` clamps to 9, updates that low
  nibble, writes the persistent settings blob, and returns status internally.
- `0x075eb2 -> 0x05d28c -> 0x06111a()` returns bits 8 through 11 of the same
  settings word.
- `0x075eb4 -> 0x05d292 -> 0x061081(level)` clamps to 3, updates bits 8
  through 11, persists the blob, and returns status internally.
- `0x075e0a -> 0x05f1e6 -> 0x067534(gain)` masks the applied gain to seven
  bits before forwarding it to the audio hardware layer.
- `0x075f82 -> 0x065d29 -> 0x069429(value) -> 0x06d63f(value)` clamps the
  applied backlight value to 15, stores it, and invokes lower resident
  backlight service `0x006fa2`.

This confirms the logical ranges, the difference between persisted logical
levels and mapped hardware values, and the getter failure sentinel used by
the common runtime.

## Cross-application evidence

The exact volume and brightness tables appear once, adjacent to each other,
in G1, G2, G3, G4, SY, EBOOK, MM, UB, and all four numbered GAM samples.
They are absent from LD and TM.

Short-instruction-anchor matching independently finds candidates for the
handlers:

| Image | Init | Volume | Brightness |
|---|---:|---:|---:|
| G1 | `0x0dd1fc` | `0x0dd715` | `0x0dd984` |
| G2 | `0x0ce752` | `0x0cecd5` | `0x0cef49` |
| G3 | `0x0cc81d` | `0x0ccf0d` | `0x0cd181` |
| G4 | `0x0cd48a` | `0x0cdaa0` | `0x0cdd14` |
| SY | `0x0d9eae` | `0x0da431` | `0x0da6a5` |
| MM | `0x22b7af` | `0x22bdf3` | `0x22c065` |
| UB | `0x224821` | `0x224b40` | `0x224db4` |

The G2/G3/G4/SY candidates have long identical instruction runs and roughly
43–49% whole-function aligned word equality in the volume/brightness
handlers despite relocated calls and data references. MM, UB, and the older
GAMs show a related older variant. Candidate addresses remain leads until
their function boundaries are verified in Ghidra.

Reproducible evidence:

- `research/reports/system-control-data-fingerprints.json`
- `research/reports/g1-common-runtime-function-candidates.json`
- `tools/re/find_system_control_tables.py`
- `tools/re/locate_relocated_functions.py`

## Clean-room API implications

A homebrew-facing equivalent should separate policy from presentation:

- `mg2_system_controls_init`
- `mg2_system_controls_poll`
- `mg2_volume_get` / `mg2_volume_set`
- `mg2_brightness_get` / `mg2_brightness_set`
- `mg2_poweroff_request`
- callbacks for drawing and hiding an original status overlay

The logical ranges and input behavior above are sufficiently recovered to
implement compatible behavior. The bundled u'nSP compiler has now been shown
to generate the correct far-call form from absolute C function pointers, and
an experimental resident adapter compiles and assembles. Its reconstructed
prototypes and behavior still need hardware validation. Until that
validation, homebrew can use the portable policy with an existing low-level
backend and original graphics and sounds. See `research/notes/02_resident_services.md`.
