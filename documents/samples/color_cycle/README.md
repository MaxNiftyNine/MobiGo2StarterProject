# MobiGo 2 color-cycle MBA demo

This is a deliberately minimal Generalplus unSP C program. It displays a solid
320x240 RGB565 framebuffer and cycles through eight colors. The MBA entry is
implemented as a resident application launch routine. It stays active because
returning tells LD that the app exited, while preserving IRQ/FIQ and servicing
the watchdog so the retail hardware services continue running.
Each color is expanded with system DMA fixed-source mode into the
physical SDRAM framebuffer addresses already configured by the retail launcher;
the program does not hard-code an emulator allocation.
The PPU mode register is set to the GPL16250VA SDK frame-base RGB565 value
`0x0088` (including bottom-to-top scanout);
unlike an earlier emulator assumption, bit 0 is not an enable bit on this chip.
The DMA control value is `0x0089`, including the SDK's normal-interrupt-mode
bit, and completion is read from `P_DMA_INT` with a bounded timeout.

The program deliberately contains no initialized global or static variables.
The MBA entry jumps directly into `main()` without the usual C runtime data-copy
startup. Color timing uses loop-local state, so no OS-owned RAM is claimed for
persistent state and behavior does not depend on RTC emulation.

`tools/build.ps1` is intended for the Windows machine with Generalplus unSP IDE
4.1.1 installed. The compiled binary is embedded at the verified G1 entry point
inside the stock `135804G1.MBA` container by the toolkit's MBA packer.
