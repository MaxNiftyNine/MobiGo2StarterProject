#ifndef MOBIGO_SDK_AUDIO_H
#define MOBIGO_SDK_AUDIO_H

#include "mobigo_sdk/system_controls.h"

enum {
    MG_SDK_SOUND_STATE_PLAYING = 2
};

/*
 * Convert the resident playback-state values used by the common runtime:
 * 1 = playing, 0 = not playing, -1 = unknown/error state.
 */
int mg_sdk_sound_state_is_playing(mg_sdk_u16 resident_state);

#endif
