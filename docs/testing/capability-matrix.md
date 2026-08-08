# Capability and evidence matrix

Last reconciled: **2026-08-08**.

This is the single current status ledger. “Verified” names the environment in
which the behavior was observed; it does not convert reverse-engineered behavior
into an official platform guarantee.

| Capability | Host/target | Emulator | Physical MobiGo 2 | Current guidance |
| --- | --- | --- | --- | --- |
| Unified CLI and manifest | Unit tested; native Windows and Wine Unix target paths | Builds role-aware command | N/A | Canonical |
| Donor-free SY MBA | Format/CRC/target build tested | Normal role-aware boot and copied-NAND route | Reported on tested hardware; system replacement remains high risk | Default new-project profile |
| Donor-free G1 MBA | Format/CRC/target build tested | Role-aware legacy route | G1 callback behavior observed on tested hardware | Legacy opt-in only |
| Resident lifecycle | Target compiled | Setup/step/finalize integration checks | Exercised by guided suite/application runs | Supported |
| Conservative title RAM | Compile-time ranges and overlap helpers | Graphics/audio/resource integrations | Maintained arena exercised on tested hardware | Supported within documented range |
| Standard controls convenience | Portable policy tests plus target build | Volume/brightness overlays; Off submission precedes terminal request but a displayed Off frame is not guaranteed | Setting application evidence exists; terminal power behavior needs broader revision coverage | Canonical, keep terminal claims bounded |
| Direct-loop controls | Target compile plus portable policy coverage | Raw matrix edges drive persisted settings/apply/power request; no resident overlay | Matrix/settings services have bounded evidence; revise across more hardware | Use only when resident UI/lifecycle is not stepped |
| Logical buttons/keyboard | Portable input tests | Scripted matrix and resident edge checks | Game controls exercised on tested unit | Supported |
| Touch queue | Portable parser tests | Scripted contact integration | Limited guided evidence; broader calibration coverage desirable | Supported with stated calibration boundary |
| Accelerometer | Driver/firmware evidence | Bosch-compatible I²C model, device tests, and interactive digital tilt | Board/device variants not fully surveyed | Emulator-inferred for portability |
| Family-A/B graphics | Authoring tests and target build | Deterministic frame/animation checks | Generated graphics and animation exercised | Supported |
| Dynamic font/text | Generator and target build | Dynamic-slot/frame checks | Exercised in guided graphics run | Supported |
| PCM8/S/ADPCM36 effects | Authoring tests and target build | State and output integration checks | Audible playback observed | Supported; analog edges still limited |
| M sequenced music | Writer/patch tests and target build | Automatic SPU beat and music checks | Audible playback observed | Supported subset |
| Existing-file storage | Packing/unit tests | Read/write/truncate/seek/remove on copied NAND | Read-only existing-file path exercised | Supported with safety boundary |
| Fresh file publication | Allocation path reached | Directory entry not reliably rediscovered | Fresh diagnostic path did not persist reliably | Experimental/unknown |
| Asynchronous MBA relaunch | Target compile and lifecycle checks | Scheduling/finalization verified for bundled region fixtures | Restart observed on bounded fixtures; arbitrary regional paths unavailable target-side | Terminal operation; other regions Unknown |
| Low-level framebuffer/watchdog/DMA | Target-only API and target build | Hardware accuracy/watchdog tests plus sample use | Core inherited framebuffer/watchdog/DMA path observed | Supported for deliberate low-level ports |
| Raw matrix helpers | Target-only API and target build | Matrix model/scripted checks | Matrix cells based on physical/firmware evidence | Prefer resident keys |
| Complete sample projects | Reproducible SY/G1 target builds | Color Cycle, movie player, and Celeste boot through real firmware; role, payload progress, input, changing frames, Off, and transient NAND are checked | Prior project-specific runs exist; current automated gate is emulator-only | Run `make sample-emulator-check` |
| Emulator accurate mode | Configuration tests | Real-time pacing plus diagnostic history; globally separate D-pad/motion mapping | Comparison mode, not proof of all silicon | Use for release comparison |
| Emulator fast mode | Configuration tests | Uncapped run and reduced history bookkeeping with identical guest input/peripherals | N/A | Use for iteration |
| USB mailbox model | USB tests/tooling | Enumeration, transport, firmware-mediated read/write and read-back | Physical tools supported on macOS/Windows; Linux backend absent | Advanced; preserve recovery data |
| Ghidra MBA/GAM loader | Extension build/import evidence | N/A | N/A | Supported analysis tool |

## Open evidence boundaries

- Fresh-file directory publication and complete NAND/FTL behavior.
- Exact analog audio output, envelope, and ADPCM36 edge behavior.
- Complete row-zoom/transform PPU behavior and TFT electrical fields.
- Every timer/counter selector, rare descriptor field, and secondary resource
  control without an independent caller.
- Hardware revision/region coverage for shutdown, relaunch, touch calibration,
  and accelerometer variants.

See [Known limitations](../reference/known-limitations.md) for design impact.
