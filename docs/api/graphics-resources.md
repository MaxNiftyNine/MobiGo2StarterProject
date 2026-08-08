# Graphics and resource API

## Linked bundles: `resource_bundle.h`

This header defines the version-2 bundle layout and helpers for:

- reading and writing 32-bit word pairs;
- converting tagged relative pointers;
- constructing primary and secondary relative references;
- sizing and populating auto-instance tables;
- reading created handles from those tables.

Registration relocates a mutable graph in place. Validate counts and storage
before writing pointer tables.

## Graphics records: `resource_graphics.h`

Portable accessors and builders cover Family-B records, component references,
bitmap descriptors, chunk dimensions, RGB555 packing, and 2-bpp word packing.

Builders return failure for unsupported geometry or insufficient output state.
Use the dimension helpers before allocating a generated graph.

## UI objects: `ui_family_b.h`

The portable object helpers prepare, show, hide, start, and stop a mutable
Family-B object. Animation uses record duration and delta fields maintained by
the resident timeline.

Callers must retrieve a valid resident object pointer from its handle before
using portable object-field helpers.

## Resident resources: `resident_resources.h`

Target operations include:

- registering the primary linked bundle;
- registering and unregistering dynamic slots;
- creating and destroying Family-A or Family-B objects;
- retrieving resident object storage;
- creating a Family-B object from a dynamic slot.

An invalid handle must be treated as creation failure. Destroy owned objects
before unregistering their dynamic bundle.

## Settings presentation

`settings_overlay.h` exposes the verified object-field policy used by the
generated settings presentation. Most applications should let
`standard_controls.h` own those objects.

See [Graphics and assets](../guides/graphics-assets.md) for authoring and memory
placement.
