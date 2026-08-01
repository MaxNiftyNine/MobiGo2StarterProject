#include "mobigo_sdk/resident_touch.h"
#include "mobigo_sdk/resident_addresses.h"

typedef const mg_sdk_u16 *(*resident_get_touch_pointer_fn)(void);
typedef mg_sdk_u16 (*resident_get_touch_count_fn)(void);

#define RESIDENT_GET_TOUCH_POINTER \
    ((resident_get_touch_pointer_fn)MG_SDK_RESIDENT_GET_TOUCH_EVENT_PTR)
#define RESIDENT_GET_TOUCH_COUNT \
    ((resident_get_touch_count_fn)MG_SDK_RESIDENT_GET_TOUCH_EVENT_COUNT)

const mg_sdk_u16 *mg_sdk_resident_touch_event_words(void)
{
    return RESIDENT_GET_TOUCH_POINTER();
}

mg_sdk_u16 mg_sdk_resident_touch_event_count(void)
{
    return RESIDENT_GET_TOUCH_COUNT();
}

static const mg_sdk_u16 *resident_touch_event_words(void *user)
{
    (void)user;
    return mg_sdk_resident_touch_event_words();
}

static mg_sdk_u16 resident_touch_event_count(void *user)
{
    (void)user;
    return mg_sdk_resident_touch_event_count();
}

const struct mg_sdk_touch_backend
    mg_sdk_experimental_resident_touch_backend = {
        resident_touch_event_words,
        resident_touch_event_count
    };
