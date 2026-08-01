#ifndef MOBIGO_SDK_RESIDENT_INPUT_H
#define MOBIGO_SDK_RESIDENT_INPUT_H

#include "mobigo_sdk/input.h"

/*
 * Experimental target-only input adapter for the resident service table.
 * Input policy is host-tested; resident prototypes still require hardware
 * validation in a clean-room executable.
 */
extern const struct mg_sdk_input_backend
    mg_sdk_experimental_resident_input_backend;

#endif
