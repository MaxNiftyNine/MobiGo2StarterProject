#include "mobigo_sdk/resident_audio.h"
#include "mobigo_sdk/resident_addresses.h"

typedef void (*resident_register_audio_resources_fn)(
    mg_sdk_u16 *title_resource_root,
    mg_sdk_u16 *shared_patch_root);
typedef mg_sdk_u32 (*resident_play_sound_fn)(
    mg_sdk_u32 resource,
    mg_sdk_u16 gain,
    mg_sdk_u16 pan,
    mg_sdk_u16 repeat,
    mg_sdk_u16 mode);
typedef int (*resident_get_sound_state_fn)(
    mg_sdk_u32 handle,
    mg_sdk_u16 *state);
typedef mg_sdk_u32 (*resident_play_music_fn)(
    mg_sdk_u32 resource,
    mg_sdk_u16 level,
    mg_sdk_u16 repeat,
    mg_sdk_u16 mode);
typedef int (*resident_music_handle_fn)(mg_sdk_u32 handle);
typedef int (*resident_music_get_u16_fn)(mg_sdk_u32 handle, mg_sdk_u16 *value);
typedef int (*resident_music_set_u16_fn)(mg_sdk_u32 handle, mg_sdk_u16 value);

#define RESIDENT_PLAY_SOUND \
    ((resident_play_sound_fn)MG_SDK_RESIDENT_PLAY_SOUND)
#define RESIDENT_REGISTER_AUDIO_RESOURCES \
    ((resident_register_audio_resources_fn)MG_SDK_RESIDENT_REGISTER_AUDIO_RESOURCES)
#define RESIDENT_GET_SOUND_STATE \
    ((resident_get_sound_state_fn)MG_SDK_RESIDENT_GET_SOUND_STATE)
#define RESIDENT_PLAY_MUSIC \
    ((resident_play_music_fn)MG_SDK_RESIDENT_PLAY_MUSIC)
#define RESIDENT_PAUSE_MUSIC \
    ((resident_music_handle_fn)MG_SDK_RESIDENT_PAUSE_MUSIC)
#define RESIDENT_RESUME_MUSIC \
    ((resident_music_handle_fn)MG_SDK_RESIDENT_RESUME_MUSIC)
#define RESIDENT_STOP_MUSIC \
    ((resident_music_handle_fn)MG_SDK_RESIDENT_STOP_MUSIC)
#define RESIDENT_GET_MUSIC_STATE \
    ((resident_music_get_u16_fn)MG_SDK_RESIDENT_GET_MUSIC_STATE)
#define RESIDENT_SET_MUSIC_REPEAT \
    ((resident_music_set_u16_fn)MG_SDK_RESIDENT_SET_MUSIC_REPEAT)
#define RESIDENT_GET_MUSIC_LEVEL \
    ((resident_music_get_u16_fn)MG_SDK_RESIDENT_GET_MUSIC_LEVEL)
#define RESIDENT_SET_MUSIC_LEVEL \
    ((resident_music_set_u16_fn)MG_SDK_RESIDENT_SET_MUSIC_LEVEL)

void mg_sdk_resident_register_audio_resources(
    mg_sdk_u16 *title_resource_root,
    mg_sdk_u16 *shared_patch_root)
{
    RESIDENT_REGISTER_AUDIO_RESOURCES(title_resource_root, shared_patch_root);
}

mg_sdk_u32 mg_sdk_resident_play_sound(
    mg_sdk_u32 resource,
    mg_sdk_u16 gain,
    mg_sdk_u16 pan,
    mg_sdk_u16 repeat,
    mg_sdk_u16 mode)
{
    return RESIDENT_PLAY_SOUND(resource, gain, pan, repeat, mode);
}

int mg_sdk_resident_get_sound_state(
    mg_sdk_u32 handle,
    mg_sdk_u16 *state)
{
    return RESIDENT_GET_SOUND_STATE(handle, state);
}

int mg_sdk_resident_sound_is_playing(mg_sdk_u32 handle)
{
    mg_sdk_u16 state = 0xffff;
    /* Physical hardware confirmed that the service's return register is not
     * a portable success boolean. The written state is the useful result. */
    mg_sdk_resident_get_sound_state(handle, &state);
    return state == MG_SDK_SOUND_STATE_PLAYING;
}

mg_sdk_u32 mg_sdk_resident_play_music(
    mg_sdk_u32 resource,
    mg_sdk_u16 level,
    mg_sdk_u16 repeat,
    mg_sdk_u16 mode)
{
    return RESIDENT_PLAY_MUSIC(resource, level, repeat, mode);
}

int mg_sdk_resident_pause_music(mg_sdk_u32 handle)
{
    return RESIDENT_PAUSE_MUSIC(handle);
}

int mg_sdk_resident_resume_music(mg_sdk_u32 handle)
{
    return RESIDENT_RESUME_MUSIC(handle);
}

int mg_sdk_resident_stop_music(mg_sdk_u32 handle)
{
    return RESIDENT_STOP_MUSIC(handle);
}

int mg_sdk_resident_get_music_state(mg_sdk_u32 handle, mg_sdk_u16 *state)
{
    return RESIDENT_GET_MUSIC_STATE(handle, state);
}

int mg_sdk_resident_set_music_repeat(mg_sdk_u32 handle, mg_sdk_u16 repeat)
{
    return RESIDENT_SET_MUSIC_REPEAT(handle, repeat);
}

int mg_sdk_resident_get_music_level(mg_sdk_u32 handle, mg_sdk_u16 *level)
{
    return RESIDENT_GET_MUSIC_LEVEL(handle, level);
}

int mg_sdk_resident_set_music_level(mg_sdk_u32 handle, mg_sdk_u16 level)
{
    return RESIDENT_SET_MUSIC_LEVEL(handle, level);
}
