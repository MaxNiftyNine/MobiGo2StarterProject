#ifndef MOBIGO_SDK_RESIDENT_RESOURCES_H
#define MOBIGO_SDK_RESIDENT_RESOURCES_H

#include "mobigo_sdk/resource_bundle.h"

typedef mg_sdk_u32 mg_sdk_ui_handle;

#define MG_SDK_INVALID_UI_HANDLE ((mg_sdk_ui_handle)0xffffffffUL)

/*
 * Target bindings to the recovered resident asset/UI services.
 *
 * register_asset_bundle accepts exactly three far pointers. Official titles
 * pass the linked header, a title-supplied primary storage base, and usually a
 * null secondary base. The service mutates relative pointers in the bundle.
 */
void mg_sdk_resident_register_asset_bundle(
    void *bundle_header,
    void *primary_storage_base,
    void *secondary_storage_base);

/*
 * Register a secondary runtime bundle in one of the resident dynamic slots.
 * Direct resident decompilation proves a seven-slot pool (slots 1..7); slot 0
 * is reserved for the application's primary bundle. The entry point accepts
 * exactly two far pointers and internally uses no secondary-storage base. It
 * returns slot 1..7, or 0 on failure.
 */
mg_sdk_u16 mg_sdk_resident_register_dynamic_bundle(
    void *bundle_header,
    void *primary_storage_base);

/*
 * Unregister a dynamic slot and destroy resident family-A/family-B objects
 * owned by that slot. Slot zero is the normal application bundle and is not
 * managed through this API.
 */
void mg_sdk_resident_unregister_dynamic_bundle(mg_sdk_u16 slot);

/*
 * Create a family-B object using a descriptor ID from an explicit dynamic
 * bundle slot. EBOOK callers pass a normal 32-bit descriptor ID.
 */
mg_sdk_ui_handle mg_sdk_ui_b_create_from_dynamic_bundle(
    mg_sdk_u16 slot,
    mg_sdk_u32 descriptor_id);

/*
 * Official callers pass a 32-bit descriptor ID with a zero high word. In the
 * normal resident path the low word is the primary-bundle descriptor index.
 */
mg_sdk_ui_handle mg_sdk_ui_a_create(mg_sdk_u32 descriptor_id);

void mg_sdk_ui_a_destroy(mg_sdk_ui_handle handle);
void *mg_sdk_ui_a_get(mg_sdk_ui_handle handle);

mg_sdk_ui_handle mg_sdk_ui_b_create(mg_sdk_u32 descriptor_id);

void mg_sdk_ui_b_destroy(mg_sdk_ui_handle handle);
void *mg_sdk_ui_b_get(mg_sdk_ui_handle handle);

#endif
