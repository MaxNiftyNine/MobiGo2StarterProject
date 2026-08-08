# Clocks, timers, DMA, watchdog, and power

## System clocks

The SoC can run from a 12 MHz source, the 32.768 kHz source, or a PLL-derived
clock with a divider. Emulator2 integrates CPU cycles using live clock settings
rather than assuming a fixed instruction rate.

Instruction timing is approximate by opcode class. Hardware-visible deadlines
for timers, RTC, watchdog, ADC, video, USB suspend, and SPU beat events are
scheduled at emulated cycle boundaries.

## Timers and interrupts

Four general timers, timebases, RTC scheduling, and multiple interrupt status/
priority banks are modeled. Status fields commonly require write-one-to-clear
acknowledgment. A handler must clear both the peripheral source and any aggregate
status required by the documented path.

Exact behavior of every counter selector and priority combination remains
incomplete; prefer resident timing unless a low-level port needs a tested timer.

## System DMA

Four channels copy 16-bit words between CPU/DMA-visible addresses. The SDK
provides start, bounded wait, copy, and fill operations. Word count zero,
invalid channels/modes, unaligned destinations, and overflowing ranges are
rejected. Fixed-source mode validates one source word and the full destination
range; incrementing copy validates both ranges.

The wait helper services the watchdog and acknowledges completion. Use a timeout
appropriate to the transfer rather than an unbounded busy loop.

## Watchdog

The loader can hand off with the watchdog active. A low-level loop must call
`mg_sdk_watchdog_kick()` frequently. Repeated resets every few seconds are a
strong sign that the watchdog was inherited but not serviced.

Normal resident applications should not reconfigure watchdog control registers.

## Power and sleep

The resident owns the standard Off presentation and terminal power request.
Use `standard_controls.h` in resident applications or `direct_controls.h` in a
framebuffer-owned loop. The direct layer performs the terminal request without
an overlay. Raw sleep/power registers and boot wake behavior are not a
substitute for the application shutdown contract.

Power-off and application handoff are terminal state transitions; test them last
and record their physical evidence separately.
