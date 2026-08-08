# Choose a target profile

The slot profile affects link addresses, entry behavior, MBA metadata, maximum
payload size, firmware handoff, and installation destination. It is not a label
that can be changed after linking.

## Decision table

| Profile | Use | Build choice | Install choice | Guidance |
| --- | --- | --- | --- | --- |
| SY | New applications and the starter | default / `--slot SY` | transient overlay; physical `--system` only with recovery | Canonical |
| G1 | Legacy examples or explicit Hamster Highway compatibility | `--slot G1` | `--g1` | Opt-in only |
| Root developer file | Developer-mode experiments | profile must still match its launch contract | `--root` | Advanced |
| Emulator MM overlay | Main-menu-role diagnostics | must be built for that role | emulator `--mba` | Not a slot converter |

## SY: canonical new-project target

The unified CLI builds SY unless a project explicitly says otherwise:

```sh
python3 tools/mobigo.py build
python3 tools/mobigo.py run
```

The normal run applies a role-aware transient overlay and boots it through the
matching firmware role without editing the source NAND. Use an explicit copied
NAND to validate persistent installation or filesystem behavior.

Replacing SY on a physical console changes the system application and can
interrupt normal boot. Emulator success is required but does not remove the
need for recovery backups.

## G1: legacy explicit opt-in

Several low-level and ported examples use G1 because that was the earliest
hardware-validated homebrew route. Their entry address, linker profile, payload
capacity, and install target are G1-specific.

Use G1 only when the project states that requirement. Build and install must
agree:

```sh
python3 tools/build/build_sdk_app.py path/to/main.c \
  --output-dir build/my-g1-project \
  --name MyG1Project \
  --slot G1
```

Then pass that G1-linked output to the G1 installer. Never pass the default
`build/MobiGo2Starter.MBA` to `--g1`.

Persistent NAND and USB installers verify complete launcher metadata, not just
the filename or title. They reject known cross-slot profiles. The advanced
`--allow-unverified-profile` flag permits only manually reviewed unknown
metadata; it cannot force a known SY payload into G1 or the reverse.

## Regional filenames

Firmware revisions and regions use different numeric prefixes and directory
layouts. The USB and NAND tools find the existing file ending in the selected
slot suffix and replace that exact file.

Do not write application logic, documentation, or automation that assumes a
literal regional filename. A filename found in a trace is evidence, not an API.

## Changing profile in a port

Changing from SY to G1 requires a full rebuild and another complete emulator
test. Recheck:

- code and asset capacity;
- entry and protected-address layout;
- application exit behavior;
- generated MBA role/footer;
- copied-NAND install destination;
- any test that asserts runtime addresses.

If there is no concrete G1 requirement, remain on SY.
