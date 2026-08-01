#ifndef MOBIGO_SDK_RESIDENT_AUDIO_H
#define MOBIGO_SDK_RESIDENT_AUDIO_H

#include "mobigo_sdk/audio.h"

/*
 * Resident audio facade.
 *
 * `resource` may be a small application sound-table ID (high word zero) or a
 * far pointer to a structured sound resource. The fifth resident argument is
 * repeat/loop: the completion handler uses nonzero to restart an S sequence
 * from child zero, and the same value is forwarded to the SPU repeat control.
 * `mode` remains the title-selected 0..3 allocation/playback policy field.
 */
void mg_sdk_resident_register_audio_resources(
    mg_sdk_u16 *title_resource_root,
    mg_sdk_u16 *shared_patch_root);

mg_sdk_u32 mg_sdk_resident_play_sound(
    mg_sdk_u32 resource,
    mg_sdk_u16 gain,
    mg_sdk_u16 pan,
    mg_sdk_u16 repeat,
    mg_sdk_u16 mode);

int mg_sdk_resident_get_sound_state(
    mg_sdk_u32 handle,
    mg_sdk_u16 *state);

/* Queries the written state value; it does not interpret the resident call's
 * undocumented return register as a success flag. */
int mg_sdk_resident_sound_is_playing(mg_sdk_u32 handle);

/*
 * M-resource sequencer. G1's common wrapper starts music with repeat=1 and
 * mode=3. The resident state values are 0/4 stopped, 1 paused, and 2 playing.
 * Physical hardware shows that the control/query return registers must not be
 * treated as portable booleans. Validate handles and observable output/state.
 */
mg_sdk_u32 mg_sdk_resident_play_music(
    mg_sdk_u32 resource,
    mg_sdk_u16 level,
    mg_sdk_u16 repeat,
    mg_sdk_u16 mode);
int mg_sdk_resident_pause_music(mg_sdk_u32 handle);
int mg_sdk_resident_resume_music(mg_sdk_u32 handle);
int mg_sdk_resident_stop_music(mg_sdk_u32 handle);
int mg_sdk_resident_get_music_state(
    mg_sdk_u32 handle,
    mg_sdk_u16 *state);
int mg_sdk_resident_set_music_repeat(
    mg_sdk_u32 handle,
    mg_sdk_u16 repeat);
int mg_sdk_resident_get_music_level(
    mg_sdk_u32 handle,
    mg_sdk_u16 *level);
int mg_sdk_resident_set_music_level(
    mg_sdk_u32 handle,
    mg_sdk_u16 level);

#endif
