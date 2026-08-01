#include <assert.h>

#include "mobigo_sdk/audio.h"

int main(void)
{
    assert(mg_sdk_sound_state_is_playing(0) == 0);
    assert(mg_sdk_sound_state_is_playing(1) == 0);
    assert(mg_sdk_sound_state_is_playing(2) == 1);
    assert(mg_sdk_sound_state_is_playing(4) == 0);
    assert(mg_sdk_sound_state_is_playing(3) == -1);
    assert(mg_sdk_sound_state_is_playing(0xffff) == -1);
    return 0;
}
