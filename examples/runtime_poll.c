/*
 * Minimal integration example for the recovered resident runtime APIs.
 *
 * Presentation and feedback audio are deliberately absent from the current
 * system-controls resident backend. A game can copy that backend and add
 * original overlay/sound callbacks.
 */

#include "mobigo_sdk/mobigo_sdk.h"

static struct mg_sdk_system_controls controls;
static struct mg_sdk_input_pump input;

void homebrew_runtime_init(void)
{
    mg_sdk_system_controls_init(
        &controls,
        &mg_sdk_experimental_resident_backend,
        0);
    mg_sdk_input_init(
        &input,
        &mg_sdk_experimental_resident_input_backend,
        0);
}

void homebrew_runtime_poll(void)
{
    mg_sdk_input_poll(&input);
    mg_sdk_system_controls_poll(&controls);
}
