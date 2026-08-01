// Apply evidence-backed clean-room SDK names to analyzed G1 or SY programs.
// Names are descriptive and are not claimed to be original vendor symbols.
// @category MobiGo

import java.util.LinkedHashMap;
import java.util.Map;

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.Symbol;
import ghidra.program.model.symbol.SourceType;

public class ApplyMobiGoSdkNames extends GhidraScript {
    private static class Annotation {
        final String name;
        final String comment;

        Annotation(String name, String comment) {
            this.name = name;
            this.comment = comment;
        }
    }

    private Address wordAddress(long value) {
        return currentProgram.getAddressFactory()
            .getAddress(String.format("%06x", value));
    }

    private void add(
            Map<Long, Annotation> map,
            long address,
            String name,
            String comment) {
        map.put(address, new Annotation(name, comment));
    }

    private Map<Long, Annotation> g1Annotations() {
        Map<Long, Annotation> result = new LinkedHashMap<>();
        add(result, 0x0dd19eL, "sdk_post_input_event",
            "Post framework event 0x1005 and save the current resident tick.");
        add(result, 0x0dd1fcL, "sdk_system_controls_init",
            "Initialize shared volume, brightness, overlay, and Off policy.");
        add(result, 0x0dd3ccL, "sdk_input_and_system_controls_poll",
            "Translate input edges and update shared system-control policy.");
        add(result, 0x0dd632L, "sdk_system_controls_shutdown",
            "Destroy common system-control state and its overlay object.");
        add(result, 0x0dd715L, "sdk_handle_volume_keys",
            "Handle volume up/down pressed edges, persistence, gain, sound, and overlay.");
        add(result, 0x0dd984L, "sdk_handle_brightness_key",
            "Handle brightness pressed edge, persistence, backlight, sound, and overlay.");
        add(result, 0x0df873L, "sdk_queue_mapped_input_event",
            "Append one translated input event code to the seven-entry local queue.");
        add(result, 0x0df8faL, "sdk_dispatch_touch_events",
            "Dispatch four-word touch records from resident services 0x75f3a/0x75f3c.");
        add(result, 0x0df9a9L, "sdk_dispatch_game_key_edges",
            "Map Left, Right, Up, Down, Primary, Exit, and Help edges to local event codes.");
        add(result, 0x0dfa5cL, "sdk_dispatch_buffered_input_codes",
            "Translate buffered and special input codes to local events.");
        add(result, 0x0dfb49L, "sdk_dispatch_system_key_edges",
            "Map three system-key pressed edges to local event codes.");
        add(result, 0x0dfb86L, "sdk_poll_high_level_input",
            "Run game, buffered, system, and touch input dispatchers.");
        add(result, 0x0e0000L, "sdk_runtime_init",
            "Start callback for the resident six-word application descriptor.");
        add(result, 0x0e0075L, "sdk_runtime_tick_and_handoff",
            "Per-frame callback; returns zero after scheduling an MBA handoff.");
        add(result, 0x0e0211L, "sdk_update_poweroff_sequence",
            "Shared Off-key presentation, feedback-sound, and power-off sequence.");
        add(result, 0x0e15e5L, "sdk_fill_words_far",
            "Fill a far word range with a 16-bit value.");
        add(result, 0x0e1a55L, "mba_entry",
            "MBA entry: decode launcher state and run resident setup/step/finalize.");
        return result;
    }

    private Map<Long, Annotation> syAnnotations() {
        Map<Long, Annotation> result = new LinkedHashMap<>();
        add(result, 0x0d9e36L, "sdk_post_input_event",
            "SY copy of framework-event 0x1005 posting and activity timestamp.");
        add(result, 0x0d9e98L, "sdk_system_controls_init",
            "SY copy of the common system-controls initializer.");
        add(result, 0x0da07eL, "sdk_input_and_system_controls_poll",
            "SY copy of the common input and system-controls frame pump.");
        add(result, 0x0da340L, "sdk_system_controls_shutdown",
            "SY copy of the common system-controls teardown.");
        add(result, 0x0da42dL, "sdk_handle_volume_keys",
            "SY volume policy; same 0..9 behavior and layout as G1.");
        add(result, 0x0da6a3L, "sdk_handle_brightness_key",
            "SY brightness policy; same 0..3 behavior and layout as G1.");
        add(result, 0x0dce72L, "sdk_queue_mapped_input_event",
            "Append one translated input event code to the local queue.");
        add(result, 0x0dcf05L, "sdk_dispatch_touch_events",
            "Exact semantic match for G1's four-word touch queue dispatcher.");
        add(result, 0x0dcfb1L, "sdk_dispatch_game_key_edges",
            "Map Left, Right, Up, Down, Primary, Exit, and Help edges.");
        add(result, 0x0dd06dL, "sdk_dispatch_buffered_input_codes",
            "Translate buffered and special input codes.");
        add(result, 0x0dd16bL, "sdk_dispatch_system_key_edges",
            "Map three resident system-key pressed edges.");
        add(result, 0x0dd1a9L, "sdk_poll_high_level_input",
            "Run game, buffered, system, and touch input dispatchers.");
        add(result, 0x0de6f8L, "sdk_runtime_init",
            "SY start callback for the resident application descriptor.");
        add(result, 0x0de770L, "sdk_runtime_tick_and_handoff",
            "SY per-frame callback; returns zero after scheduling an MBA handoff.");
        add(result, 0x0de8bdL, "sdk_runtime_stop",
            "SY stop callback; releases the runtime's resident context.");
        add(result, 0x0de8d6L, "sdk_update_poweroff_sequence",
            "SY copy of the common Off-key and power-off sequence.");
        add(result, 0x0df6edL, "sdk_fill_words_far",
            "Byte-for-byte relocated copy of G1's far word-fill function.");
        add(result, 0x0dfc1dL, "mba_entry",
            "SY MBA entry using the resident setup/step/finalize lifecycle.");
        return result;
    }

    private Map<Long, Annotation> g2Annotations() {
        Map<Long, Annotation> result = new LinkedHashMap<>();
        add(result, 0x0ce73cL, "sdk_system_controls_init",
            "G2 common system-controls initializer; creates family-B descriptor 4.");
        add(result, 0x0cecd1L, "sdk_handle_volume_keys",
            "G2 volume handler; selects compacted settings mode 4.");
        add(result, 0x0cef47L, "sdk_handle_brightness_key",
            "G2 brightness handler; selects compacted settings mode 1.");
        return result;
    }

    private Map<Long, Annotation> g3Annotations() {
        Map<Long, Annotation> result = new LinkedHashMap<>();
        add(result, 0x0cc805L, "sdk_system_controls_init",
            "G3 common system-controls initializer; creates family-B descriptor 0x14.");
        add(result, 0x0ccf09L, "sdk_handle_volume_keys",
            "G3 volume handler; selects link-compacted settings mode 1.");
        add(result, 0x0cd17fL, "sdk_handle_brightness_key",
            "G3 brightness handler; selects link-compacted settings mode 0.");
        return result;
    }

    private Map<Long, Annotation> g4Annotations() {
        Map<Long, Annotation> result = new LinkedHashMap<>();
        add(result, 0x0cd468L, "sdk_system_controls_init",
            "G4 common system-controls initializer; creates family-B descriptor 3.");
        add(result, 0x0cda9cL, "sdk_handle_volume_keys",
            "G4 volume handler; selects link-compacted settings mode 3.");
        add(result, 0x0cdd12L, "sdk_handle_brightness_key",
            "G4 brightness handler; selects link-compacted settings mode 1.");
        return result;
    }

    private Map<Long, Annotation> g1DataAnnotations() {
        Map<Long, Annotation> result = new LinkedHashMap<>();
        add(result, 0x0e2160L, "sdk_asset_bundle_header",
            "0x20-word linked asset-bundle header registered through resident service 0x075f00.");
        add(result, 0x0f69a6L, "sdk_ui_family_b_descriptor_table",
            "G1 family-B table: 0x32 descriptors, 12 words each.");
        add(result, 0x0f6a4eL, "sdk_standard_settings_descriptor",
            "Family-B descriptor 0x0e for the shared brightness/volume overlay.");
        add(result, 0x0f6be6L, "sdk_standard_poweroff_descriptor",
            "Family-B descriptor 0x30 for the shared Off presentation.");
        add(result, 0x0f2c46L, "sdk_standard_settings_modes",
            "Five-mode settings resource reached by the family-B descriptor.");
        add(result, 0x0f2a62L, "sdk_brightness_mode_records",
            "Four 14-word brightness presentation records (settings mode 1).");
        add(result, 0x0f2bb8L, "sdk_volume_mode_records",
            "Ten 14-word volume presentation records (settings mode 4).");
        add(result, 0x0f297aL, "sdk_brightness_component_lists",
            "Brightness component lists: 32-bit count then four-word component references.");
        add(result, 0x0f29c6L, "sdk_volume_component_lists",
            "Volume component lists: 32-bit count then four-word component references.");
        add(result, 0x0e4c92L, "sdk_first_brightness_bitmap",
            "Six-word 48x32 bitmap descriptor used by the first brightness record.");
        add(result, 0x0e3634L, "sdk_first_brightness_bitmap_chunks",
            "Four-word bitmap chunks; packed dimensions and primary-relative pixel pointers.");
        add(result, 0x0f54d2L, "sdk_standard_poweroff_resource",
            "Nested resource reached by G1's standard power-off descriptor.");
        return result;
    }

    private Map<Long, Annotation> syDataAnnotations() {
        Map<Long, Annotation> result = new LinkedHashMap<>();
        add(result, 0x0f30baL, "sdk_asset_bundle_header",
            "SY 0x20-word linked asset-bundle header registered through resident service 0x075f00.");
        add(result, 0x0f91c6L, "sdk_ui_family_b_descriptor_table",
            "SY family-B table: 0x1d descriptors, 12 words each.");
        add(result, 0x0f91d2L, "sdk_standard_settings_descriptor",
            "Family-B descriptor 1 for the shared brightness/volume overlay.");
        add(result, 0x0f92daL, "sdk_standard_poweroff_descriptor",
            "Family-B descriptor 0x17 for the shared Off presentation.");
        add(result, 0x0f4982L, "sdk_standard_settings_modes",
            "Five-mode settings resource reached by the family-B descriptor.");
        add(result, 0x0f479eL, "sdk_brightness_mode_records",
            "Four 14-word brightness presentation records (settings mode 1).");
        add(result, 0x0f48f4L, "sdk_volume_mode_records",
            "Ten 14-word volume presentation records (settings mode 4).");
        add(result, 0x0f46b2L, "sdk_brightness_component_lists",
            "SY brightness component lists matching the G1 schema.");
        add(result, 0x0f4702L, "sdk_volume_component_lists",
            "SY volume component lists matching the G1 schema.");
        add(result, 0x0f3cccL, "sdk_first_brightness_bitmap",
            "SY six-word 48x32 bitmap descriptor for the first brightness record.");
        add(result, 0x0f3172L, "sdk_first_brightness_bitmap_chunks",
            "SY bitmap chunks with packed dimensions and primary-relative pixel pointers.");
        add(result, 0x0f761aL, "sdk_standard_poweroff_resource",
            "Nested resource reached by SY's standard power-off descriptor.");
        return result;
    }

    private Map<Long, Annotation> g2DataAnnotations() {
        Map<Long, Annotation> result = new LinkedHashMap<>();
        add(result, 0x0df074L, "sdk_asset_bundle_header",
            "G2 0x20-word linked asset-bundle header.");
        add(result, 0x0e606aL, "sdk_ui_family_b_descriptor_table",
            "G2 family-B descriptor table.");
        add(result, 0x0e609aL, "sdk_standard_settings_descriptor",
            "G2 family-B settings descriptor 4.");
        add(result, 0x0e03e4L, "sdk_standard_settings_modes",
            "G2 five-mode standard settings table.");
        add(result, 0x0e0200L, "sdk_brightness_mode_records",
            "G2 four-record brightness mode 1.");
        add(result, 0x0e0356L, "sdk_volume_mode_records",
            "G2 ten-record volume mode 4.");
        add(result, 0x0e0118L, "sdk_brightness_component_lists",
            "G2 brightness component lists.");
        add(result, 0x0e0164L, "sdk_volume_component_lists",
            "G2 volume component lists.");
        add(result, 0x0df890L, "sdk_first_brightness_bitmap",
            "G2 first 48x32 brightness bitmap descriptor.");
        add(result, 0x0df174L, "sdk_first_brightness_bitmap_chunks",
            "G2 first brightness bitmap chunks.");
        return result;
    }

    private Map<Long, Annotation> g3DataAnnotations() {
        Map<Long, Annotation> result = new LinkedHashMap<>();
        add(result, 0x1f2d11L, "sdk_asset_bundle_header",
            "G3 0x20-word linked asset-bundle header.");
        add(result, 0x1f6d73L, "sdk_ui_family_b_descriptor_table",
            "G3 family-B descriptor table.");
        add(result, 0x1f6e63L, "sdk_standard_settings_descriptor",
            "G3 family-B settings descriptor 0x14.");
        add(result, 0x1f6a27L, "sdk_standard_settings_modes",
            "G3 link-compacted two-mode standard settings table.");
        add(result, 0x1f695fL, "sdk_brightness_mode_records",
            "G3 four-record brightness mode 0.");
        add(result, 0x1f6999L, "sdk_volume_mode_records",
            "G3 ten-record volume mode 1.");
        add(result, 0x1f689dL, "sdk_brightness_component_lists",
            "G3 brightness component lists; X offsets differ from G1.");
        add(result, 0x1f68d3L, "sdk_volume_component_lists",
            "G3 volume component lists; X offsets differ from G1.");
        add(result, 0x1f3ecfL, "sdk_first_brightness_bitmap",
            "G3 first 48x32 brightness bitmap descriptor.");
        add(result, 0x1f399fL, "sdk_first_brightness_bitmap_chunks",
            "G3 first brightness bitmap chunks.");
        return result;
    }

    private Map<Long, Annotation> g4DataAnnotations() {
        Map<Long, Annotation> result = new LinkedHashMap<>();
        add(result, 0x16fd39L, "sdk_asset_bundle_header",
            "G4 0x20-word linked asset-bundle header.");
        add(result, 0x175737L, "sdk_ui_family_b_descriptor_table",
            "G4 family-B descriptor table.");
        add(result, 0x17575bL, "sdk_standard_settings_descriptor",
            "G4 family-B settings descriptor 3.");
        add(result, 0x1711f1L, "sdk_standard_settings_modes",
            "G4 link-compacted four-mode standard settings table.");
        add(result, 0x1710a9L, "sdk_brightness_mode_records",
            "G4 four-record brightness mode 1.");
        add(result, 0x171163L, "sdk_volume_mode_records",
            "G4 ten-record volume mode 3.");
        add(result, 0x170fd9L, "sdk_brightness_component_lists",
            "G4 brightness component lists.");
        add(result, 0x17100dL, "sdk_volume_component_lists",
            "G4 volume component lists.");
        add(result, 0x1706afL, "sdk_first_brightness_bitmap",
            "G4 first 48x32 brightness bitmap descriptor.");
        add(result, 0x16fdd9L, "sdk_first_brightness_bitmap_chunks",
            "G4 first brightness bitmap chunks.");
        return result;
    }

    @Override
    public void run() throws Exception {
        String programName = currentProgram.getName().toUpperCase();
        Map<Long, Annotation> annotations;
        Map<Long, Annotation> dataAnnotations;
        if (programName.contains("135800G1") ||
            programName.contains("BUNDLE_G1")) {
            annotations = g1Annotations();
            dataAnnotations = g1DataAnnotations();
        }
        else if (programName.contains("135800G2") ||
                 programName.contains("BUNDLE_G2")) {
            annotations = g2Annotations();
            dataAnnotations = g2DataAnnotations();
        }
        else if (programName.contains("135800G3") ||
                 programName.contains("BUNDLE_G3")) {
            annotations = g3Annotations();
            dataAnnotations = g3DataAnnotations();
        }
        else if (programName.contains("135800G4") ||
                 programName.contains("BUNDLE_G4")) {
            annotations = g4Annotations();
            dataAnnotations = g4DataAnnotations();
        }
        else if (programName.contains("135800SY") ||
                 programName.contains("BUNDLE_SY")) {
            annotations = syAnnotations();
            dataAnnotations = syDataAnnotations();
        }
        else {
            throw new IllegalArgumentException(
                "Supported programs are BUNDLE_G1..G4 and BUNDLE_SY; got " +
                currentProgram.getName());
        }

        int applied = 0;
        for (Map.Entry<Long, Annotation> item : annotations.entrySet()) {
            monitor.checkCancelled();
            Address address = wordAddress(item.getKey());
            disassemble(address);
            Function function = getFunctionAt(address);
            if (function == null) {
                function = createFunction(address, item.getValue().name);
            }
            if (function == null) {
                printerr(String.format(
                    "Could not create function at 0x%06x", item.getKey()));
                continue;
            }
            function.setName(
                item.getValue().name, SourceType.USER_DEFINED);
            setPlateComment(address, item.getValue().comment);
            applied++;
        }
        for (Map.Entry<Long, Annotation> item : dataAnnotations.entrySet()) {
            monitor.checkCancelled();
            Address address = wordAddress(item.getKey());
            Symbol symbol = getSymbolAt(address);
            if (symbol == null) {
                createLabel(address, item.getValue().name, true);
            }
            else if (symbol.getName().startsWith("DAT_")) {
                symbol.setName(item.getValue().name, SourceType.USER_DEFINED);
            }
            setPlateComment(address, item.getValue().comment);
            applied++;
        }
        println(String.format(
            "Applied %d MobiGo SDK annotations to %s.",
            applied, currentProgram.getName()));
    }
}
