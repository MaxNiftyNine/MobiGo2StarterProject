# Examples and compatibility projects

The focused examples under this directory demonstrate one API or regression.
The complete projects show larger build and porting patterns.

| Project | Target | Purpose | System controls |
| --- | --- | --- | --- |
| `hardware_test_suite/` | SY | guided public-SDK validation on hardware | resident standard controls |
| `color_cycle/` | SY | inherited framebuffer, DMA, watchdog | direct-loop controls, no overlays |
| `mobigo_celeste/` | legacy G1 | advanced software renderer and assembly scaler | direct-loop controls, no overlays |
| `bad_apple_player/` | legacy G1 | compressed-movie/PCM technique | direct-loop controls, no overlays |

New applications should start from `app/` and remain on SY. Do not copy a G1
target merely because a complete example uses it.

Build all maintained samples with `make samples`, then boot and exercise all
three with `make sample-emulator-check`; or run one project's `build.py`.
Outputs stay under `build/`. Focused probes cover resident
lifecycle, input, resources, dynamic text, graphics, effects, sequenced music,
system UI, and storage. The maintained overview is
[`docs/examples/index.md`](../docs/examples/index.md).
