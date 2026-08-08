# LCD, framebuffer, and PPU

## Display geometry

The LCD is 320×240. The inherited frame-base path uses 16-bit RGB565 words with
a 320-word stride. Resident resource palettes use RGB555-style entries and
their own transparency conventions.

## Inherited framebuffers

The loader selects live front and back buffer addresses. Physical runs have
shown that these addresses can change; a fixed framebuffer constant is unsafe.

`mg_sdk_framebuffers_capture()` is the supported low-level query. Normal
resident applications should use resident resource and UI services.

## Frame-base ownership

`mg_sdk_framebuffer_present()` selects a captured buffer while preserving the
inherited interrupt environment. `mg_sdk_framebuffer_take_ownership()` is a
stronger operation for a program that intentionally disables PPU frame
interrupts and owns stable scanout.

Taking ownership can conflict with resident rendering. Do not use it simply to
avoid learning the resident resource API.

## PPU capabilities modeled

Emulator2 covers the main firmware-visible paths used by retail and homebrew:

- frame-base scanout;
- indexed tile/page layers;
- sprites and signed/clipped coordinates;
- direct-color tiles and linemap behavior;
- palette transparency;
- global and individual sprite blending;
- RGB fade and saturation;
- frame compare/wrap timing and local video DMA.

Row zoom and transform effects are not fully characterized. TFT electrical
timing and every register field are outside the confirmed model.

## Resident graphics

The resident uses linked Family-A and Family-B graphs rather than exposing raw
PPU programming to each title. This path is preferred for menus, text, settings,
sprites, and animation because firmware already owns composition and updates.

## Validation strategy

Frame validation should compare exact regions or expected colors after a known
instruction count. Test transparency, clipping, palette selection, and more
than one frame. A host window displaying something is weaker evidence than a
deterministic dumped-frame assertion.
