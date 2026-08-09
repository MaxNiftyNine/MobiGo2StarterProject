# Graphics, UI, and asset generation

The SDK supports two complementary rendering styles: resident resource graphs
and a low-level inherited framebuffer.

## Resident resource path

Use resident resources for menus, UI, sprites, animations, and dynamic text.
The main pieces are:

- version-2 linked resource bundles;
- Family-A background/tiled images;
- Family-B object records, components, bitmaps, and animation timelines;
- two 512-word RGB555 palette windows;
- dynamic bundle slots for text and other temporary resources.

Mutable bundle graphs must be copied to title RAM before registration. The
resident rebases tagged pointers in place and owns created UI handles until they
are destroyed or their dynamic slot is unregistered.

## Low-level framebuffer path

Existing software renderers can query the inherited launcher framebuffer through
`hardware.h`. Never assume a fixed display address. The launcher may rotate
among buffers, and the CPU and DMA use word addresses.

The physical LCD is 320×240. Scale or letterbox lower-resolution games
deliberately. For large transfers, DMA is normally faster and simpler than a C
word loop.

## Color and packing

- Framebuffer scanout commonly uses RGB565.
- Resident palettes use RGB555 and may use bit 15 for transparency.
- Family-B bitmap formats include packed indexed pixels and fixed legal chunk
  axes.
- File byte order and CPU word order must both be considered when generating
  packed data.

Use SDK packers rather than recreating bit layouts inside each project.

## Deterministic generators

Available tools generate original system UI, clean font, backgrounds,
animations, and audio resources. Examples:

```sh
python3 tools/assets/build_system_ui_bundle.py build/system-ui
python3 tools/assets/build_clean_font_bundle.py build/font
python3 tools/assets/build_family_a_background_bundle.py build/background
python3 tools/assets/build_menu_art.py build/menu-icon \
  --source assets/menu_icon.ppm
```

Generated outputs normally include C, a header, binary data, and a manifest.
Link the generated C source through the project build.

`build_menu_art.py` is the Starter-specific exception: it fits a P6 PPM source
inside 64×104, treats `#ff00ff` as transparent, quantizes it to 15 visible
colors, and writes the 32-byte RGB555 palette plus 3,328-byte packed menu tile.
The normal `menu_icon` project field runs this step automatically. Those bytes
are baked into the MBA header, which is also where Homebrew Launcher reads the
application's carousel icon.

## Asset ownership

Do not extract retail art into a clean-room application. Generated samples are
original. A port may include upstream assets only when its license and
redistribution terms allow that use; document those terms beside the project.

## Verification

Check more than a screenshot:

- bundle relocation and handle creation;
- palette and transparency values;
- clipping at all screen edges;
- animation record progression and looping;
- exact framebuffer stride and orientation;
- stable output after multiple frames;
- deterministic regeneration from a clean checkout.
