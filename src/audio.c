#include "mobigo_sdk/audio.h"

int mg_sdk_sound_state_is_playing(mg_sdk_u16 resident_state)
{
    if (resident_state == MG_SDK_SOUND_STATE_PLAYING) {
        return 1;
    }
    if (resident_state == 0 ||
        resident_state == 1 ||
        resident_state == 4) {
        return 0;
    }
    return -1;
}
