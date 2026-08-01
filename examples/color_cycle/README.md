# Color cycle

This minimal G1 sample cycles the MobiGo 2 screen through eight RGB565 colors.
It demonstrates taking the active framebuffer addresses from the launcher,
using GPL16250VA system DMA, keeping display interrupts enabled, and servicing
the watchdog. It is intentionally low-level; most applications should use the
resident graphics APIs instead.

Build a complete donor-free MBA from the repository root:

```sh
python3 examples/color_cycle/build.py
```

The output is `build/color-cycle/ColorCycle.MBA`. Add `--install-nand` to also
make a NAND image with the sample installed in the G1 slot.

The sample uses the SDK's standard compiler, linker body, MBA packer, and NAND
installer. It has no private `.bdy`, copied retail data, or platform-specific
PowerShell build path.
