// Seed MobiGo resident-service trampolines and their implementation targets.
// Run headless scripts with a Ghidra-supported JDK (JDK 21 for Ghidra 11.3).
// @category MobiGo

import java.util.HashMap;
import java.util.Map;

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.SourceType;

public class SeedResidentServices extends GhidraScript {
    private static final long TABLE_BASE = 0x075c00L;
    private static final long TABLE_END = 0x075fe0L;

    private Map<Long, String> names() {
        Map<Long, String> result = new HashMap<>();
        result.put(0x075c52L, "register_dynamic_asset_bundle");
        result.put(0x075c54L, "unregister_dynamic_asset_bundle");
        result.put(0x075c58L, "create_dynamic_ui_family_b_object");
        result.put(0x075e06L, "register_audio_resources");
        result.put(0x075e0aL, "apply_master_volume");
        result.put(0x075e0eL, "play_sound");
        result.put(0x075e1aL, "get_sound_state");
        result.put(0x075e2cL, "play_music");
        result.put(0x075e32L, "pause_music");
        result.put(0x075e34L, "resume_music");
        result.put(0x075e36L, "stop_music");
        result.put(0x075e38L, "get_music_state");
        result.put(0x075e3cL, "set_music_repeat");
        result.put(0x075e3eL, "get_music_level");
        result.put(0x075e40L, "set_music_level");
        result.put(0x075e5eL, "request_poweroff");
        result.put(0x075e60L, "get_system_keys");
        result.put(0x075e62L, "system_key_down");
        result.put(0x075e64L, "system_key_pressed");
        result.put(0x075e66L, "system_key_released");
        result.put(0x075e7cL, "create_context");
        result.put(0x075e7eL, "destroy_context");
        result.put(0x075e82L, "get_context_pointer");
        result.put(0x075e84L, "release_context");
        result.put(0x075e8aL, "post_framework_event");
        result.put(0x075eaaL, "get_volume");
        result.put(0x075eacL, "set_volume");
        result.put(0x075eb2L, "get_brightness");
        result.put(0x075eb4L, "set_brightness");
        result.put(0x075ec6L, "get_game_keys");
        result.put(0x075ec8L, "game_key_down");
        result.put(0x075ecaL, "game_key_pressed");
        result.put(0x075eccL, "game_key_released");
        result.put(0x075ee0L, "get_input_event_pointer");
        result.put(0x075ee2L, "get_input_event_count");
        result.put(0x075ee6L, "test_special_key");
        result.put(0x075efaL, "ui_runtime_init");
        result.put(0x075efcL, "ui_runtime_shutdown");
        result.put(0x075efeL, "ui_runtime_render_frame");
        result.put(0x075f00L, "register_asset_bundle");
        result.put(0x075f02L, "load_ui_family_a_descriptor");
        result.put(0x075f04L, "init_ui_family_a_descriptor_runtime");
        result.put(0x075f06L, "create_ui_family_a_object");
        result.put(0x075f08L, "destroy_ui_family_a_object");
        result.put(0x075f0eL, "get_ui_family_a_object");
        result.put(0x075f10L, "load_ui_family_b_descriptor");
        result.put(0x075f12L, "create_ui_family_b_object");
        result.put(0x075f14L, "destroy_ui_family_b_object");
        result.put(0x075f18L, "get_ui_family_b_object");
        result.put(0x075f1cL, "bind_ui_object_control");
        result.put(0x075f2eL, "get_ticks");
        result.put(0x075f30L, "touch_init");
        result.put(0x075f32L, "touch_shutdown");
        result.put(0x075f34L, "touch_update");
        result.put(0x075f36L, "touch_get_enabled");
        result.put(0x075f38L, "touch_set_enabled");
        result.put(0x075f3aL, "get_touch_event_pointer");
        result.put(0x075f3cL, "get_touch_event_count");
        result.put(0x075f3eL, "touch_clear_records");
        result.put(0x075f40L, "touch_register_handler");
        result.put(0x075f42L, "touch_unregister_handler");
        result.put(0x075f44L, "touch_reset_handlers");
        result.put(0x075f46L, "runtime_setup");
        result.put(0x075f48L, "runtime_step");
        result.put(0x075f4aL, "runtime_finalize");
        result.put(0x075f52L, "gpio_b_bit9_hardware_init");
        result.put(0x075f82L, "apply_backlight");
        result.put(0x075fa2L, "file_open");
        result.put(0x075fa4L, "file_close");
        result.put(0x075fa6L, "file_read");
        result.put(0x075fa8L, "file_write");
        result.put(0x075faaL, "file_truncate_at_position");
        result.put(0x075facL, "file_seek_absolute");
        result.put(0x075faeL, "file_size");
        result.put(0x075fb0L, "file_stat");
        result.put(0x075fb2L, "path_remove");
        result.put(0x075fb4L, "path_exists");
        result.put(0x075fa0L, "get_volume_prefix");
        result.put(0x075fb4L, "path_exists");
        result.put(0x075fcaL, "launch_mba");
        result.put(0x075fccL, "query_launch_volume");
        return result;
    }

    private int word(Address address) throws Exception {
        return getShort(address) & 0xffff;
    }

    private Address wordAddress(long value) {
        return currentProgram.getAddressFactory()
            .getAddress(String.format("%06x", value));
    }

    @Override
    public void run() throws Exception {
        Map<Long, String> workingNames = names();
        int active = 0;
        int placeholders = 0;

        for (long service = TABLE_BASE; service < TABLE_END; service += 2) {
            monitor.checkCancelled();
            Address entry = wordAddress(service);
            int opcode = word(entry);
            /*
             * The unSP language displays word addresses but Ghidra's raw
             * memory API advances this Address object in bytes.
             */
            int low = word(entry.add(2));
            if ((opcode & 0xffc0) != 0xfe80) {
                printerr(String.format(
                    "invalid resident trampoline at 0x%06x", service));
                continue;
            }
            long targetValue = ((long)(opcode & 0x3f) << 16) | low;
            if (service == TABLE_BASE || service == 0x075e0aL) {
                println(String.format(
                    "trampoline diagnostic 0x%06x: %04x %04x -> 0x%06x",
                    service, opcode, low, targetValue));
            }
            Address target = wordAddress(targetValue);
            boolean placeholder = targetValue == service;
            String suffix = workingNames.get(service);
            String entryName = suffix == null
                ? String.format("resident_service_%06x", service)
                : "resident_" + suffix;

            disassemble(entry);
            Function trampoline = getFunctionAt(entry);
            if (trampoline == null) {
                trampoline = createFunction(entry, entryName);
            }
            else if (suffix != null) {
                trampoline.setName(entryName, SourceType.USER_DEFINED);
            }
            setEOLComment(
                entry,
                placeholder
                    ? "Unimplemented resident-service self-loop placeholder."
                    : String.format(
                        "Resident-service trampoline to 0x%06x.", targetValue));

            if (placeholder) {
                placeholders++;
                continue;
            }
            active++;
            disassemble(target);
            Function implementation = getFunctionAt(target);
            if (implementation == null) {
                String targetName = suffix == null
                    ? String.format("resident_impl_%06x", service)
                    : "resident_impl_" + suffix;
                createFunction(target, targetName);
            }
        }
        println(String.format(
            "Seeded %d active resident services and %d placeholders.",
            active, placeholders));
    }
}
