#ifndef MOBIGO_SDK_RESIDENT_BACKEND_H
#define MOBIGO_SDK_RESIDENT_BACKEND_H

#include "mobigo_sdk/system_controls.h"

/*
 * Experimental target-only adapter for the fixed resident service bank.
 *
 * These entry points are supported by strong static evidence but have not yet
 * been exercised by this clean-room implementation on hardware. Do not call
 * this backend on a host computer or when the MobiGo resident service module
 * is not present at 0x075xxx.
 *
 * Overlay and feedback-sound callbacks are intentionally left null. Homebrew
 * can provide original presentation callbacks by copying this backend and
 * filling those fields.
 */
extern const struct mg_sdk_system_backend
    mg_sdk_experimental_resident_backend;

#endif
