# Application launch and handoff

Official games do not return to a universal in-process menu. They ask the
resident environment to launch another MBA, including the separate SY system
menu, MM media manager, and UB USB application.

## Resident launcher

Service `0x075fca` is a trampoline to implementation `0x05aaf7`. Direct
resident decompilation recovers its effective C interface:

```c
void resident_launch_mba(
    const char *path,
    unsigned short argument_count,
    const unsigned long *arguments);
```

Pointers are 32-bit far pointers and `unsigned long` is 32 bits under the
Generalplus compiler bundled with the integrated starter project.

The implementation:

1. copies the path byte by byte into two internal buffers;
2. stops at a NUL byte or after 42 bytes;
3. clamps `argument_count` to 16;
4. copies each argument as a two-word/32-bit value;
5. records the argument count;
6. sets an internal launch-pending flag.

This is an asynchronous handoff request rather than an immediate far jump.
The common runtime later observes the flag and completes teardown/launch.
The title's current frame callback must return zero after scheduling the
request. G1's recovered frame wrapper follows exactly that path, allowing the
outer entry loop to stop and call resident finalization; the MBA entry then
returns. SY independently follows the same sequence when launching its selected
MBA. Both verified G1-to-SY and SY-to-title transitions use one 32-bit argument
whose value is `999`. Continuing to return one leaves the launch pending while
the current title keeps running; spinning after finalization prevents the
resident caller from regaining control.

## G1 examples

`sdk_return_to_system_menu` at G1 `0x0e0668` calls:

```text
path: A:\BUNDLE\SY\135800SY.MBA
argument_count: 1
arguments[0]: 999
```

`sdk_launch_media_manager` and `sdk_launch_usb_app` resolve MM/UB paths and
call the same service with zero arguments.

The corresponding target API is:

- `mg_sdk_resident_launch_mba`
- `MG_SDK_LAUNCH_PATH_BYTES`
- `MG_SDK_LAUNCH_MAX_ARGUMENTS`

It is declared in `include/mobigo_sdk/application.h`.

## Path testing

Service `0x075fb4` dispatches to `0x06aac8` and returns nonzero when a path is
available. It accepts the same far string-pointer representation as the
launcher. If the path is not already volume-qualified, the resident
implementation can build and test a qualified form.

The clean-room wrapper is `mg_sdk_resident_path_exists`.

G1 obtains a volume/path descriptor through `0x075fa0`. That service fills a
multi-field structure by querying internal selectors 1 through 7 and
`0x0c..0x0e`; its public structure layout is not yet sufficiently recovered.
Consequently, automatic volume-prefix construction remains internal to G1's
recovered `sdk_build_volume_path` and is not exposed in the clean-room header.
