# Boot flow and application slots

## Normal boot path

The internal ROM initializes the platform and loads additional firmware from
SPI/NAND. The user-visible flow continues through boot animation, loading
application, and menu/system modules before an MBA application entry is called.

An MBA application is entered as a callback inside a live firmware environment.
It is not a reset image. The launcher can leave display interrupts, watchdog,
resident services, and memory state active.

## Supported slot profiles

The builder has deterministic metadata profiles for SY and legacy G1. Each
profile fixes:

- runtime image base and body load address;
- application entry;
- protected callback/data ranges;
- maximum payload capacity and complete file size;
- launcher role and footer metadata.

Changing only the header entry does not relocate code. Build the payload and
container for the same profile.

## SY

SY is the canonical new-project profile and normal unified-CLI target. Routine
emulator runs overlay the discovered system role in memory. An explicit copied
NAND replaces the discovered system application and validates persistent
installation through normal boot.

Physical replacement is inherently high risk because a bad system application
can prevent normal startup. It requires recovery backups and complete emulator
validation.

## G1

G1 is retained for legacy compatibility and maintained examples. It is not the
default template for a new port. Build it explicitly and install only through
the discovered G1 target.

## Exit and handoff

A top-level return leaves the current MBA. For asynchronous relaunch, schedule
the request, return zero from the frame callback, finalize resident runtime, and
return from the entry. A permanent loop or continued nonzero frames can prevent
the handoff.

## Diagnostic shortcuts

The unified CLI's role-aware transient overlay is the canonical application
smoke-test path. A claim about persistent install, slot discovery, or
filesystem behavior additionally needs copied-NAND validation because the
overlay does not test that storage contract. Forced-PC/handoff shortcuts remain
diagnostic only.
