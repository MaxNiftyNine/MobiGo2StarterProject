# Graphics and resource callables

## `resource_bundle.h` — portable linked-graph helpers

```c
mg_sdk_u32 mg_sdk_bundle_read_word_pair(
    const mg_sdk_u16 *words,
    mg_sdk_u16 word_offset);

void mg_sdk_bundle_write_word_pair(
    mg_sdk_u16 *words,
    mg_sdk_u16 word_offset,
    mg_sdk_u32 value);

mg_sdk_u32 mg_sdk_bundle_relative_to_word_address(
    mg_sdk_u32 header_word_address,
    mg_sdk_u32 relative_word_pointer);

mg_sdk_u32 mg_sdk_bundle_primary_relative(mg_sdk_u32 word_offset);
mg_sdk_u32 mg_sdk_bundle_secondary_relative(mg_sdk_u32 word_offset);

mg_sdk_u16 mg_sdk_bundle_auto_instance_table_words(
    mg_sdk_u16 descriptor_count);

void mg_sdk_bundle_auto_instance_set_marker(
    mg_sdk_u16 *table,
    mg_sdk_u16 descriptor_index,
    mg_sdk_u32 marker);

mg_sdk_u32 mg_sdk_bundle_auto_instance_read_handle(
    const mg_sdk_u16 *table,
    mg_sdk_u16 descriptor_count,
    mg_sdk_u16 descriptor_index);
```

The word-pair helpers read/write little-word-order 32-bit fields in caller
storage. `mg_sdk_bundle_relative_to_word_address()` rebases an untagged offset
from the first word after the 32-word header. The primary/secondary helpers add
the appropriate tag while masking to that tag's offset width.

An auto-instance table has parallel two-word marker and handle arrays, so
`mg_sdk_bundle_auto_instance_table_words()` returns four words per descriptor.
`mg_sdk_bundle_auto_instance_set_marker()` writes the marker side;
`mg_sdk_bundle_auto_instance_read_handle()` reads the resident-populated handle
side. Callers own and size all arrays; these helpers do not bounds-check.

**Evidence:** portable/host-tested against generated graphs; relocation and
auto-instantiation have firmware-emulator coverage. Unknown header words remain
opaque.

## `resource_graphics.h` — Family-B timeline records

```c
mg_sdk_s16 mg_sdk_ui_b_record_delta_x(
    const struct mg_sdk_ui_b_record *record);
mg_sdk_s16 mg_sdk_ui_b_record_delta_y(
    const struct mg_sdk_ui_b_record *record);
mg_sdk_u16 mg_sdk_ui_b_record_duration(
    const struct mg_sdk_ui_b_record *record);
mg_sdk_s16 mg_sdk_ui_b_record_min_x(
    const struct mg_sdk_ui_b_record *record);
mg_sdk_s16 mg_sdk_ui_b_record_max_x(
    const struct mg_sdk_ui_b_record *record);
mg_sdk_s16 mg_sdk_ui_b_record_min_y(
    const struct mg_sdk_ui_b_record *record);
mg_sdk_s16 mg_sdk_ui_b_record_max_y(
    const struct mg_sdk_ui_b_record *record);

void mg_sdk_ui_b_record_build(
    struct mg_sdk_ui_b_record *record,
    mg_sdk_s16 delta_x,
    mg_sdk_s16 delta_y,
    mg_sdk_u16 duration,
    mg_sdk_s16 min_y,
    mg_sdk_s16 max_y,
    mg_sdk_s16 min_x,
    mg_sdk_s16 max_x,
    mg_sdk_u32 event_token,
    mg_sdk_u32 component_pointer,
    mg_sdk_u32 runtime_slot_pointer);
```

The seven accessors return signed deltas/bounds or the unsigned duration from a
caller-supplied 14-word record. `mg_sdk_ui_b_record_build()` fills the complete
known layout, zeros reserved word 7, and writes the event/component/runtime
word pairs. The two pointer arguments are normally bundle-relative before
registration; the runtime slot must refer to private zeroed mutable storage.
The builder ignores a null output; accessors require a valid record.

## `resource_graphics.h` — components and bitmap descriptors

```c
mg_sdk_s16 mg_sdk_component_x_offset(
    const struct mg_sdk_component_reference *component);
mg_sdk_s16 mg_sdk_component_y_offset(
    const struct mg_sdk_component_reference *component);

void mg_sdk_component_build(
    struct mg_sdk_component_reference *component,
    mg_sdk_s16 x_offset,
    mg_sdk_s16 y_offset,
    mg_sdk_u32 bitmap_pointer);

mg_sdk_u16 mg_sdk_bitmap_width(
    const struct mg_sdk_bitmap_descriptor *bitmap);
mg_sdk_u16 mg_sdk_bitmap_height(
    const struct mg_sdk_bitmap_descriptor *bitmap);
mg_sdk_u16 mg_sdk_bitmap_format_code(
    const struct mg_sdk_bitmap_descriptor *bitmap);
mg_sdk_u16 mg_sdk_bitmap_bits_per_pixel(
    const struct mg_sdk_bitmap_descriptor *bitmap);
mg_sdk_u16 mg_sdk_bitmap_palette_selector(
    const struct mg_sdk_bitmap_descriptor *bitmap);
mg_sdk_u16 mg_sdk_bitmap_uses_extended_palette(
    const struct mg_sdk_bitmap_descriptor *bitmap);

mg_sdk_u16 mg_sdk_bitmap_pack_format(
    mg_sdk_u16 format_code,
    mg_sdk_u16 palette_selector,
    mg_sdk_u16 use_extended_palette);

mg_sdk_u16 mg_sdk_bitmap_default_sprite_palette_index(
    const struct mg_sdk_bitmap_descriptor *bitmap);

void mg_sdk_bitmap_build(
    struct mg_sdk_bitmap_descriptor *bitmap,
    mg_sdk_u16 format_word,
    mg_sdk_u16 width,
    mg_sdk_u16 height,
    mg_sdk_u32 chunk_table_pointer);

mg_sdk_u16 mg_sdk_rgb555_pack(
    mg_sdk_u16 red,
    mg_sdk_u16 green,
    mg_sdk_u16 blue,
    mg_sdk_u16 transparent);
```

Component accessors return signed offsets; `mg_sdk_component_build()` writes
offsets and a linked bitmap pointer. Bitmap accessors decode the six-word
descriptor. `mg_sdk_bitmap_bits_per_pixel()` maps supported format codes to
2/4/6/8 and returns zero for an unknown code.

`mg_sdk_bitmap_pack_format()` combines the format, 4-bit palette selector, and
extended-bank flag. `mg_sdk_bitmap_default_sprite_palette_index()` converts the
descriptor selection into the default resident sprite palette index.
`mg_sdk_bitmap_build()` initializes format, geometry, reserved zero, and chunk
table pointer. `mg_sdk_rgb555_pack()` masks each channel to five bits and sets
bit 15 when transparency is nonzero. Builders ignore null outputs; accessors
require valid caller-owned records.

## `resource_graphics.h` — bitmap chunks and 2-bpp words

```c
mg_sdk_u16 mg_sdk_bitmap_chunk_width(
    const struct mg_sdk_bitmap_chunk *chunk);
mg_sdk_u16 mg_sdk_bitmap_chunk_height(
    const struct mg_sdk_bitmap_chunk *chunk);
mg_sdk_u16 mg_sdk_bitmap_chunk_axis_supported(mg_sdk_u16 dimension);
mg_sdk_u16 mg_sdk_bitmap_chunk_dimensions_supported(
    mg_sdk_u16 width,
    mg_sdk_u16 height);
mg_sdk_u16 mg_sdk_bitmap_pack_chunk_dimensions(
    mg_sdk_u16 width,
    mg_sdk_u16 height);

int mg_sdk_bitmap_chunk_build(
    struct mg_sdk_bitmap_chunk *chunk,
    mg_sdk_u16 width,
    mg_sdk_u16 height,
    mg_sdk_u16 flags,
    mg_sdk_u32 primary_data_pointer);

mg_sdk_u16 mg_sdk_bitmap_pack_2bpp_word(const mg_sdk_u16 *pixels);
mg_sdk_u16 mg_sdk_bitmap_unpack_2bpp_pixel(
    mg_sdk_u16 packed,
    mg_sdk_u16 index);
```

Chunk width/height decode the packed low/high bytes. Axis support returns true
only for 16, 32, or 64 pixels; dimension support requires both axes.
`mg_sdk_bitmap_chunk_build()` returns one for a written four-word chunk and zero
for null output or unsupported dimensions. Data pointers use the tagged primary
class before registration.

`mg_sdk_bitmap_pack_2bpp_word()` consumes eight caller-owned palette indices.
`mg_sdk_bitmap_unpack_2bpp_pixel()` returns index `0..7` and zero for an
out-of-range index. Chunk/packing behavior is portable and host-tested;
renderer constraints are firmware-derived and emulator-verified.

## `ui_family_b.h` — mutable resident object prefix

```c
void mg_sdk_ui_b_object_prepare(
    struct mg_sdk_ui_b_object *object,
    mg_sdk_s16 x,
    mg_sdk_s16 y,
    mg_sdk_u16 state_3);

void mg_sdk_ui_b_object_show(
    struct mg_sdk_ui_b_object *object,
    mg_sdk_u16 mode,
    mg_sdk_u16 record,
    mg_sdk_s16 x,
    mg_sdk_s16 y);

void mg_sdk_ui_b_object_play_animation(
    struct mg_sdk_ui_b_object *object,
    mg_sdk_u16 mode,
    mg_sdk_u16 record,
    mg_sdk_s16 x,
    mg_sdk_s16 y,
    mg_sdk_u16 loop);

void mg_sdk_ui_b_object_stop_animation(
    struct mg_sdk_ui_b_object *object);

void mg_sdk_ui_b_object_hide(struct mg_sdk_ui_b_object *object);
```

Prepare initializes the known mutable prefix hidden at a position with stopped,
non-looping animation. Show selects one bundle-local mode/record and makes it
visible. Play additionally clears the stopped flag and applies the loop flag;
stop freezes the current record; hide clears visibility.

The pointer must be valid resident object storage obtained from a successful
`mg_sdk_ui_b_get()` (or a layout-compatible generated object). These void
helpers do not validate handles or null pointers. Fields are renderer-confirmed;
timeline transitions have deterministic emulator coverage.

## `settings_overlay.h` — typed Family-B settings view

```c
void mg_sdk_settings_object_prepare(
    struct mg_sdk_settings_object *object,
    mg_sdk_s16 x,
    mg_sdk_s16 y);

void mg_sdk_settings_object_show(
    struct mg_sdk_settings_object *object,
    mg_sdk_u16 mode,
    mg_sdk_u16 record,
    mg_sdk_s16 x,
    mg_sdk_s16 y);

void mg_sdk_settings_object_hide(struct mg_sdk_settings_object *object);
```

These delegate to the layout-compatible Family-B operations with standard
settings state. Mode/record IDs are bundle-local, not global SDK constants.
The pointer and object lifetime follow the Family-B rules above. Most
applications should let `standard_controls.h` own these calls.

## `resident_resources.h` — target bundle and object services

```c
void mg_sdk_resident_register_asset_bundle(
    void *bundle_header,
    void *primary_storage_base,
    void *secondary_storage_base);

mg_sdk_u16 mg_sdk_resident_register_dynamic_bundle(
    void *bundle_header,
    void *primary_storage_base);

void mg_sdk_resident_unregister_dynamic_bundle(mg_sdk_u16 slot);

mg_sdk_ui_handle mg_sdk_ui_b_create_from_dynamic_bundle(
    mg_sdk_u16 slot,
    mg_sdk_u32 descriptor_id);

mg_sdk_ui_handle mg_sdk_ui_a_create(mg_sdk_u32 descriptor_id);
void mg_sdk_ui_a_destroy(mg_sdk_ui_handle handle);
void *mg_sdk_ui_a_get(mg_sdk_ui_handle handle);

mg_sdk_ui_handle mg_sdk_ui_b_create(mg_sdk_u32 descriptor_id);
void mg_sdk_ui_b_destroy(mg_sdk_ui_handle handle);
void *mg_sdk_ui_b_get(mg_sdk_ui_handle handle);
```

Primary registration mutates relative pointers in caller-owned writable graph
storage and returns no status. Dynamic registration returns slot `1..7` or zero;
unregistering a slot destroys its resident-owned Family-A/B objects. Do not keep
handles or pointers after unregister.

Create calls return an opaque 32-bit handle or `MG_SDK_INVALID_UI_HANDLE`.
`mg_sdk_ui_a_get()` and `mg_sdk_ui_b_get()` return a resident pointer for a valid
handle; do not free it or retain it after destroy. Destroy only objects the
application owns. Descriptor IDs are bundle-local, with an explicit slot for
the dynamic Family-B creator.

These calls are target-only typed resident bindings. Registration, dynamic
font, Family-A/B creation, and animation are emulator-verified; physical
coverage is reported per generated resource rather than assumed for every
descriptor field.
