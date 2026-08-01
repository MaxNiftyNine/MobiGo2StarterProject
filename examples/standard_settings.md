# Original standard-settings bundle

`tools/assets/build_standard_settings_bundle.py` generates a complete clean-room
version-2 linked resource graph for a brightness/volume overlay. It consumes no
official MBA and draws new 64-by-32 sun, meter, speaker, and volume indicators
programmatically.

Generate the binary and directly compilable C forms with:

```sh
python3 tools/assets/build_standard_settings_bundle.py \
    build/clean_settings \
    --prefix mobigo_clean_settings
```

The output contains:

- `bundle.bin`: mutable header and bundle-relative object graph;
- `primary.bin`: two 512-entry RGB555 palette sources followed by packed 2-bpp
  pixels;
- `mobigo_clean_settings_resources.c/.h`: the same data as linkable u'nSP C
  arrays plus registration and creation helpers;
- `manifest.json`: generated mode indices, labels, offsets, hashes, and sizes;
- `previews/*.pgm`: original source artwork previews.

Basic target use is:

```c
#include "mobigo_clean_settings_resources.h"

mg_sdk_ui_handle settings;

mobigo_clean_settings_copy_bundle(writable_bundle);
mobigo_clean_settings_register(writable_bundle);
settings = mobigo_clean_settings_create();
```

The descriptor ID is zero, the brightness mode is zero, and the volume mode is
one. These are generated bundle-local constants in the header, not global
resident SDK numbers. Registration mutates linked pointers, so copy the const
template to a fresh writable title-RAM graph and register that copy only once.

The emitted graph reproduces the recovered official structure:

```text
version-2 header
  -> 14-entry chunk directory
  -> family-B settings descriptor
       -> two-mode table
            -> 4 brightness records
            -> 10 volume records
                 -> component list
                 -> bitmap descriptor
                 -> chunk entry
                 -> tagged primary pixel data
                 -> private two-word runtime slot
```

Host tests validate all relative/tagged pointers, build the generated C with a
strict C99 compiler, and ensure no generated pixel payload hash matches the 13
retail settings payloads. `make target-check` also compiles the generated
resources with Generalplus u'nSP tools.

The graph is structurally derived from five official titles and the resident
registration/renderer paths. It is runtime-verified through the retail
resident registrar and renderer in the emulator. Physical-console validation
remains pending.
