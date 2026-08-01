#ifndef MOBIGO_SDK_RESIDENT_TOUCH_H
#define MOBIGO_SDK_RESIDENT_TOUCH_H

#include "mobigo_sdk/touch.h"

const mg_sdk_u16 *mg_sdk_resident_touch_event_words(void);
mg_sdk_u16 mg_sdk_resident_touch_event_count(void);

extern const struct mg_sdk_touch_backend
    mg_sdk_experimental_resident_touch_backend;

#endif
