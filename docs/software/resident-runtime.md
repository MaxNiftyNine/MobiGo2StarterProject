# Resident firmware and ABI

Official applications share a fixed resident service bank and common lifecycle,
input, UI, audio, storage, and application-handoff behavior. Public SDK names
are clean-room descriptions; they are not vendor symbol claims.

## Service categories

The typed SDK wrappers cover:

- runtime setup, step, and finalize;
- current/down/pressed/released game and system keys;
- buffered keyboard events and touch records;
- volume, brightness, backlight, and power operations;
- primary and dynamic resource-bundle registration;
- Family-A and Family-B object creation/access/destruction;
- UI initialization and frame rendering;
- audio resource registration, effects, music, state, repeat, and level;
- packed-path storage operations;
- path tests and asynchronous MBA launch.

## Fixed addresses and typed wrappers

`resident_addresses.h` centralizes strongly supported service word addresses.
Application code should call the typed wrapper from the related header. A raw
address does not establish arguments, return registers, clobbers, or ownership.

Unresolved entries remain absent or explicitly named as unknown rather than
receiving invented prototypes.

## Calling environment

The Generalplus compiler uses target-specific far calls and word-addressed
pointers. Host C tests cannot call resident services. Portable policy and
resource constructors are separated so they can receive ordinary host tests.

## Lifecycle ordering

A normal application:

1. initializes owned memory;
2. performs resident runtime setup;
3. copies and registers mutable resource graphs;
4. creates UI/audio state;
5. runs callbacks through resident step;
6. destroys project-owned objects as required;
7. finalizes before returning or handing off.

Skipping setup or calling target wrappers outside the resident environment is
unsupported.

## Evidence

Resident bindings are accepted when cross-title static evidence and executable
firmware behavior agree. Physical coverage is tracked per subsystem rather than
claimed for the entire ABI at once.
