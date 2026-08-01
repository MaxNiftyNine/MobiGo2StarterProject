#include "mobigo_sdk/resident_resources.h"
#include "mobigo_sdk/resident_addresses.h"

typedef void (*resident_register_asset_bundle_fn)(
    void *bundle_header,
    void *primary_storage_base,
    void *secondary_storage_base);
typedef mg_sdk_u16 (*resident_register_dynamic_bundle_fn)(
    void *bundle_header,
    void *primary_storage_base);
typedef void (*resident_unregister_dynamic_bundle_fn)(mg_sdk_u16 slot);
typedef mg_sdk_ui_handle (*resident_create_dynamic_ui_b_fn)(
    mg_sdk_u16 slot,
    mg_sdk_u32 descriptor_id);
typedef mg_sdk_ui_handle (*resident_create_ui_fn)(mg_sdk_u32 descriptor_id);
typedef void (*resident_destroy_ui_fn)(mg_sdk_ui_handle handle);
typedef void *(*resident_get_ui_fn)(mg_sdk_ui_handle handle);

#define RESIDENT_REGISTER_ASSET_BUNDLE \
    ((resident_register_asset_bundle_fn) \
        MG_SDK_RESIDENT_REGISTER_ASSET_BUNDLE)
#define RESIDENT_REGISTER_DYNAMIC_BUNDLE \
    ((resident_register_dynamic_bundle_fn) \
        MG_SDK_RESIDENT_REGISTER_DYNAMIC_BUNDLE)
#define RESIDENT_UNREGISTER_DYNAMIC_BUNDLE \
    ((resident_unregister_dynamic_bundle_fn) \
        MG_SDK_RESIDENT_UNREGISTER_DYNAMIC_BUNDLE)
#define RESIDENT_CREATE_DYNAMIC_UI_FAMILY_B \
    ((resident_create_dynamic_ui_b_fn) \
        MG_SDK_RESIDENT_CREATE_DYNAMIC_UI_FAMILY_B)
#define RESIDENT_CREATE_UI_FAMILY_A \
    ((resident_create_ui_fn)MG_SDK_RESIDENT_CREATE_UI_FAMILY_A)
#define RESIDENT_DESTROY_UI_FAMILY_A \
    ((resident_destroy_ui_fn)MG_SDK_RESIDENT_DESTROY_UI_FAMILY_A)
#define RESIDENT_GET_UI_FAMILY_A \
    ((resident_get_ui_fn)MG_SDK_RESIDENT_GET_UI_FAMILY_A)
#define RESIDENT_CREATE_UI_FAMILY_B \
    ((resident_create_ui_fn)MG_SDK_RESIDENT_CREATE_UI_FAMILY_B)
#define RESIDENT_DESTROY_UI_FAMILY_B \
    ((resident_destroy_ui_fn)MG_SDK_RESIDENT_DESTROY_UI_FAMILY_B)
#define RESIDENT_GET_UI_FAMILY_B \
    ((resident_get_ui_fn)MG_SDK_RESIDENT_GET_UI_FAMILY_B)

void mg_sdk_resident_register_asset_bundle(
    void *bundle_header,
    void *primary_storage_base,
    void *secondary_storage_base)
{
    RESIDENT_REGISTER_ASSET_BUNDLE(
        bundle_header, primary_storage_base, secondary_storage_base);
}

mg_sdk_u16 mg_sdk_resident_register_dynamic_bundle(
    void *bundle_header,
    void *primary_storage_base)
{
    return RESIDENT_REGISTER_DYNAMIC_BUNDLE(
        bundle_header, primary_storage_base);
}

void mg_sdk_resident_unregister_dynamic_bundle(mg_sdk_u16 slot)
{
    RESIDENT_UNREGISTER_DYNAMIC_BUNDLE(slot);
}

mg_sdk_ui_handle mg_sdk_ui_b_create_from_dynamic_bundle(
    mg_sdk_u16 slot,
    mg_sdk_u32 descriptor_id)
{
    return RESIDENT_CREATE_DYNAMIC_UI_FAMILY_B(slot, descriptor_id);
}

mg_sdk_ui_handle mg_sdk_ui_a_create(mg_sdk_u32 descriptor_id)
{
    return RESIDENT_CREATE_UI_FAMILY_A(descriptor_id);
}

void mg_sdk_ui_a_destroy(mg_sdk_ui_handle handle)
{
    RESIDENT_DESTROY_UI_FAMILY_A(handle);
}

void *mg_sdk_ui_a_get(mg_sdk_ui_handle handle)
{
    return RESIDENT_GET_UI_FAMILY_A(handle);
}

mg_sdk_ui_handle mg_sdk_ui_b_create(mg_sdk_u32 descriptor_id)
{
    return RESIDENT_CREATE_UI_FAMILY_B(descriptor_id);
}

void mg_sdk_ui_b_destroy(mg_sdk_ui_handle handle)
{
    RESIDENT_DESTROY_UI_FAMILY_B(handle);
}

void *mg_sdk_ui_b_get(mg_sdk_ui_handle handle)
{
    return RESIDENT_GET_UI_FAMILY_B(handle);
}
