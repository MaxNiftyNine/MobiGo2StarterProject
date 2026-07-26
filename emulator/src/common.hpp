#pragma once
/*
 * mobigo2_emu - GPL16250 / unSP-based VTech MobiGo 2 emulator.
 *
 * CPU interpreter portions are a clean standalone port of documented unSP
 * ISA 1.2 behavior with reference to MAME's GPL-2.0+ unSP core by
 * Segher Boessenkool, Ryan Holtz, and David Haywood. This file is therefore
 * distributed under GPL-2.0-or-later.
 *
 * Hardware map/register names are from the supplied Generalplus manuals and
 * MAME's BSD-3-Clause GPL16250 notes. Where behavior is not documented, source
 * comments say ASSUMPTION and runtime logs keep the firmware-visible access.
 */

#include <SDL.h>

#include <algorithm>
#include <array>
#include <bit>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <deque>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_set>
#include <vector>

namespace mobigo {

constexpr uint32_t kAddrMask = 0x3fffff;      // unSP 22-bit word address
constexpr uint32_t kPpuAddrHighMask = 0x07ff; // PPU FREE mode exposes a 27-bit word address.
constexpr uint32_t kWordCount = 0x400000;
constexpr uint32_t kCsBase = 0x030000;        // GPAC800/GPL16250 NAND variant external chip-select base.
constexpr uint32_t kSdramWords = 0x400000;    // EM638165TS-6G: 4M x16 SDRAM, 64 Mbit / 8 MiB.
constexpr uint32_t kMmioBase = 0x007000;
constexpr uint32_t kMmioEnd = 0x007fff;
constexpr uint16_t UNSP_N = 0x0200;
constexpr uint16_t UNSP_Z = 0x0100;
constexpr uint16_t UNSP_S = 0x0080;
constexpr uint16_t UNSP_C = 0x0040;

inline std::ofstream g_log;

constexpr uint64_t kDefaultRenderInterval = 50000;
constexpr int kDefaultInstructionBatch = 20000;
// Frame-base PPU rendering is hardware work, not an instantaneous register
// side effect. Give firmware enough elapsed device time to observe the busy
// bit and service intervening video/timer IRQs before completion latches.
constexpr uint64_t kPpuJobCycles = 160000;

inline uint32_t ppu_frame_addr(uint16_t low, uint16_t high) {
    // Verified SDK examples require FBI_ADDR[26:0] to be 16-word aligned;
    // the low four address bits are hard-wired to zero.
    return uint32_t(low & 0xfff0) | ((uint32_t(high) & kPpuAddrHighMask) << 16);
}

[[noreturn]] inline void die(const std::string &msg) {
    throw std::runtime_error(msg);
}

inline std::vector<uint8_t> read_file_bytes(const std::filesystem::path &path) {
    std::ifstream f(path, std::ios::binary);
    if (!f) die("failed to open " + path.string());
    f.seekg(0, std::ios::end);
    const auto size = f.tellg();
    f.seekg(0, std::ios::beg);
    std::vector<uint8_t> out(static_cast<size_t>(size));
    if (!out.empty()) f.read(reinterpret_cast<char *>(out.data()), static_cast<std::streamsize>(out.size()));
    return out;
}

inline void write_file_bytes_atomic(const std::filesystem::path &path,
                                    const std::vector<uint8_t> &bytes) {
    std::filesystem::path temporary = path;
    temporary += ".tmp";
    {
        std::ofstream f(temporary, std::ios::binary | std::ios::trunc);
        if (!f) die("failed to open " + temporary.string());
        if (!bytes.empty())
            f.write(reinterpret_cast<const char *>(bytes.data()),
                    static_cast<std::streamsize>(bytes.size()));
        if (!f) die("failed while writing " + temporary.string());
    }
    std::error_code ec;
    const auto permissions = std::filesystem::status(path, ec).permissions();
    if (!ec) std::filesystem::permissions(temporary, permissions, ec);
    ec.clear();
    std::filesystem::rename(temporary, path, ec);
    if (ec) {
        std::filesystem::remove(temporary);
        die("failed to replace " + path.string() + ": " + ec.message());
    }
}

inline uint16_t le16(const std::vector<uint8_t> &v, size_t byte) {
    if (byte + 1 >= v.size()) return 0xffff;
    return uint16_t(v[byte] | (v[byte + 1] << 8));
}

inline std::vector<uint16_t> bytes_to_words(const std::vector<uint8_t> &v, bool big_endian) {
    std::vector<uint16_t> out((v.size() + 1) / 2, 0xffff);
    for (size_t i = 0; i < out.size(); ++i) {
        const size_t byte = i * 2;
        if (byte + 1 >= v.size()) out[i] = 0xffff;
        else if (big_endian) out[i] = uint16_t((v[byte] << 8) | v[byte + 1]);
        else out[i] = le16(v, byte);
    }
    return out;
}

struct ScriptedTouch {
    uint64_t at = 0;
    uint64_t duration = 0;
    uint16_t x = 0;
    uint16_t y = 0;
};

struct ScriptedKeyTransition {
    uint64_t at = 0;
    unsigned row = 0;
    unsigned column = 0;
    bool pressed = false;
    std::string name;
};

struct Options {
    std::filesystem::path rom = "internalrom.bin";
    std::filesystem::path cart;
    std::filesystem::path spi = "spi.bin";
    std::filesystem::path nand = "nand.bin";
    std::filesystem::path mba;
    std::filesystem::path dump_frame;
    std::filesystem::path dump_current_frame;
    std::filesystem::path dump_frame_dir;
    std::filesystem::path dump_memory;
    std::filesystem::path dump_code;
    uint32_t dump_memory_base = 0;
    uint32_t dump_memory_words = 0;
    uint32_t dump_code_base = 0;
    uint32_t dump_code_words = 0;
    uint64_t max_steps = 0;
    uint64_t render_interval = kDefaultRenderInterval;
    uint32_t max_present_hz = 60;
    uint64_t open_window_at = 0;
    uint64_t start_logging_at = 0;
    uint64_t dump_frame_interval = 0;
    uint64_t trace_limit = 0;
    uint64_t trace_transition_limit = 0;
    uint64_t trace_start_insn = 0;
    std::vector<ScriptedTouch> scripted_touches;
    std::vector<ScriptedKeyTransition> scripted_key_transitions;
    uint32_t trace_lo = 0;
    uint32_t trace_hi = 0;
    uint32_t rom_base = 0x008000;
    uint32_t start_pc = 0;
    std::string boot = "rom";
    std::string rom_endian = "le";
    bool trace = false;
    bool trace_transitions = false;
    bool trace_range = false;
    bool dump_memory_dma = false;
    bool start_pc_set = false;
    bool rom_shadow_low = false;
    bool rom_fetch_mirror64 = false;
    bool allow_invalid_alu_nop = false;
    bool auto_power_wake = true;
    bool log = false;
    bool vsync = false;
    uint16_t efuse0 = 0;
    uint16_t efuse1 = 0;
    uint16_t efuse2 = 0x0300;
    uint16_t gpio_a = 0x7fff;
    uint16_t gpio_b = 0xfffe;
    uint16_t gpio_c = 0xfeff;
    uint16_t gpio_d = 0xffff;
    uint16_t gpio_e = 0x0000;
    uint16_t battery_adc = 0x0500;
    bool window = true;
    bool audio = false;
    bool usb = false;
    std::filesystem::path log_path = "emulator.log";
};

inline Options parse_args(int argc, char **argv) {
    Options opt;
    for (int i = 1; i < argc; ++i) {
        std::string a = argv[i];
        auto need = [&](const char *name) -> std::string {
            if (i + 1 >= argc) die(std::string("missing value for ") + name);
            return argv[++i];
        };
        if (a == "--rom") opt.rom = need("--rom");
        else if (a == "--cart") opt.cart = need("--cart");
        else if (a == "--spi") opt.spi = need("--spi");
        else if (a == "--nand") opt.nand = need("--nand");
        else if (a == "--mba") opt.mba = need("--mba");
        else if (a == "--boot") opt.boot = need("--boot");
        else if (a == "--rom-base") opt.rom_base = uint32_t(std::stoul(need("--rom-base"), nullptr, 0));
        else if (a == "--rom-endian") opt.rom_endian = need("--rom-endian");
        else if (a == "--start-pc") {
            opt.start_pc = uint32_t(std::stoul(need("--start-pc"), nullptr, 0)) & kAddrMask;
            opt.start_pc_set = true;
        }
        else if (a == "--steps") opt.max_steps = std::stoull(need("--steps"));
        else if (a == "--render-interval") opt.render_interval = std::stoull(need("--render-interval"));
        else if (a == "--max-present-hz") opt.max_present_hz = uint32_t(
            std::stoul(need("--max-present-hz")));
        else if (a == "--open-window-at") opt.open_window_at = std::stoull(need("--open-window-at"));
        else if (a == "--start-logging-at") opt.start_logging_at = std::stoull(need("--start-logging-at"));
        else if (a == "--dump-frame") opt.dump_frame = need("--dump-frame");
        else if (a == "--dump-current-frame") opt.dump_current_frame = need("--dump-current-frame");
        else if (a == "--dump-frame-dir") opt.dump_frame_dir = need("--dump-frame-dir");
        else if (a == "--dump-frame-interval") opt.dump_frame_interval = std::stoull(need("--dump-frame-interval"));
        else if (a == "--touch-event") {
            const std::string value = need("--touch-event");
            std::array<std::string, 4> fields;
            size_t start = 0;
            for (size_t field = 0; field < fields.size(); ++field) {
                const size_t comma = value.find(',', start);
                if (field + 1 < fields.size() && comma == std::string::npos)
                    die("--touch-event expects at,duration,x,y");
                if (field + 1 == fields.size() && comma != std::string::npos)
                    die("--touch-event expects exactly four values");
                fields[field] = value.substr(
                    start, comma == std::string::npos ? comma : comma - start);
                start = comma == std::string::npos ? value.size() : comma + 1;
            }
            ScriptedTouch touch;
            touch.at = std::stoull(fields[0]);
            touch.duration = std::stoull(fields[1]);
            touch.x = uint16_t(std::stoul(fields[2]));
            touch.y = uint16_t(std::stoul(fields[3]));
            if (touch.duration == 0 || touch.x >= 320 || touch.y >= 240)
                die("--touch-event requires nonzero duration and LCD coordinates x<320,y<240");
            opt.scripted_touches.push_back(touch);
        }
        else if (a == "--key-event") {
            const std::string value = need("--key-event");
            std::array<std::string, 3> fields;
            size_t start = 0;
            for (size_t field = 0; field < fields.size(); ++field) {
                const size_t comma = value.find(',', start);
                if (field + 1 < fields.size() && comma == std::string::npos)
                    die("--key-event expects at,duration,key");
                if (field + 1 == fields.size() && comma != std::string::npos)
                    die("--key-event expects exactly three values");
                fields[field] = value.substr(
                    start, comma == std::string::npos ? comma : comma - start);
                start = comma == std::string::npos ? value.size() : comma + 1;
            }
            const uint64_t at = std::stoull(fields[0]);
            const uint64_t duration = std::stoull(fields[1]);
            if (duration == 0) die("--key-event requires nonzero duration");
            std::string key = fields[2];
            std::transform(key.begin(), key.end(), key.begin(),
                           [](unsigned char c) { return char(std::tolower(c)); });
            unsigned row = 0;
            unsigned column = 0;
            if (key == "t") { row = 0; column = 0; }
            else if (key == "y") { row = 0; column = 1; }
            else if (key == "u") { row = 0; column = 2; }
            else if (key == "i") { row = 0; column = 3; }
            else if (key == "o") { row = 0; column = 4; }
            else if (key == "p") { row = 0; column = 5; }
            else if (key == "w") { row = 0; column = 6; }
            else if (key == "e") { row = 0; column = 7; }
            else if (key == "r") { row = 0; column = 8; }
            else if (key == "f") { row = 1; column = 0; }
            else if (key == "g") { row = 1; column = 1; }
            else if (key == "h") { row = 1; column = 2; }
            else if (key == "j") { row = 1; column = 3; }
            else if (key == "k") { row = 1; column = 4; }
            else if (key == "l") { row = 1; column = 5; }
            else if (key == "a") { row = 1; column = 6; }
            else if (key == "s") { row = 1; column = 7; }
            else if (key == "d") { row = 1; column = 8; }
            else if (key == "c") { row = 2; column = 0; }
            else if (key == "v") { row = 2; column = 1; }
            else if (key == "b") { row = 2; column = 2; }
            else if (key == "n") { row = 2; column = 3; }
            else if (key == "m") { row = 2; column = 4; }
            else if (key == "del") { row = 2; column = 5; }
            else if (key == "caps") { row = 2; column = 6; }
            else if (key == "z") { row = 2; column = 7; }
            else if (key == "x") { row = 2; column = 8; }
            else if (key == "leftarrow") { row = 3; column = 0; }
            else if (key == "space") { row = 3; column = 1; }
            else if (key == "off") { row = 3; column = 2; }
            else if (key == "left") { row = 3; column = 3; }
            else if (key == "up") { row = 3; column = 4; }
            else if (key == "primary") { row = 3; column = 5; }
            else if (key == "q") { row = 3; column = 6; }
            else if (key == "num") { row = 3; column = 7; }
            else if (key == "rightarrow") { row = 4; column = 0; }
            else if (key == "enter") { row = 4; column = 1; }
            else if (key == "exit") { row = 4; column = 2; }
            else if (key == "right") { row = 4; column = 3; }
            else if (key == "down") { row = 4; column = 4; }
            else if (key == "help") { row = 4; column = 5; }
            else if (key == "brightness") { row = 4; column = 6; }
            else if (key == "voldown") { row = 4; column = 7; }
            else if (key == "volup") { row = 4; column = 8; }
            else if (key == "question") { row = 5; column = 5; }
            else die("--key-event key name is not in the MobiGo 2 matrix map");
            opt.scripted_key_transitions.push_back({at, row, column, true, key});
            opt.scripted_key_transitions.push_back(
                {at + duration, row, column, false, key});
        }
        else if (a == "--dump-memory") opt.dump_memory = need("--dump-memory");
        else if (a == "--dump-code") opt.dump_code = need("--dump-code");
        else if (a == "--dump-memory-base") {
            opt.dump_memory_base = uint32_t(std::stoul(need("--dump-memory-base"), nullptr, 0));
        }
        else if (a == "--dump-memory-words") {
            opt.dump_memory_words = uint32_t(std::stoul(need("--dump-memory-words"), nullptr, 0));
        }
        else if (a == "--dump-code-base") {
            opt.dump_code_base = uint32_t(std::stoul(need("--dump-code-base"), nullptr, 0));
        }
        else if (a == "--dump-code-words") {
            opt.dump_code_words = uint32_t(std::stoul(need("--dump-code-words"), nullptr, 0));
        }
        else if (a == "--trace-limit") opt.trace_limit = std::stoull(need("--trace-limit"));
        else if (a == "--trace-start-insn") opt.trace_start_insn = std::stoull(need("--trace-start-insn"));
        else if (a == "--trace-pc") {
            opt.trace_lo = uint32_t(std::stoul(need("--trace-pc lo"), nullptr, 0));
            opt.trace_hi = uint32_t(std::stoul(need("--trace-pc hi"), nullptr, 0));
            opt.trace_range = true;
            opt.trace = true;
        }
        else if (a == "--trace") { opt.trace = true; opt.log = true; }
        else if (a == "--trace-transitions") {
            opt.trace_transitions = true;
            opt.log = true;
        }
        else if (a == "--trace-transition-limit") {
            opt.trace_transition_limit = std::stoull(need("--trace-transition-limit"));
        }
        else if (a == "--dump-memory-dma") opt.dump_memory_dma = true;
        else if (a == "--log") opt.log = true;
        else if (a == "--log-file") { opt.log = true; opt.log_path = need("--log-file"); }
        else if (a == "--vsync") opt.vsync = true;
        else if (a == "--no-window") opt.window = false;
        else if (a == "--audio") opt.audio = true;
        else if (a == "--usb") opt.usb = true;
        else if (a == "--rom-fetch-mirror64") opt.rom_fetch_mirror64 = true;
        else if (a == "--rom-shadow-low") opt.rom_shadow_low = true;
        else if (a == "--no-rom-shadow-low") opt.rom_shadow_low = false;
        else if (a == "--no-rom-fetch-mirror64") opt.rom_fetch_mirror64 = false;
        else if (a == "--allow-invalid-alu-nop") opt.allow_invalid_alu_nop = true;
        else if (a == "--no-auto-power-wake") opt.auto_power_wake = false;
        else if (a == "--efuse0") opt.efuse0 = uint16_t(std::stoul(need("--efuse0"), nullptr, 0));
        else if (a == "--efuse1") opt.efuse1 = uint16_t(std::stoul(need("--efuse1"), nullptr, 0));
        else if (a == "--efuse2") opt.efuse2 = uint16_t(std::stoul(need("--efuse2"), nullptr, 0));
        else if (a == "--gpio-a") opt.gpio_a = uint16_t(std::stoul(need("--gpio-a"), nullptr, 0));
        else if (a == "--gpio-b") opt.gpio_b = uint16_t(std::stoul(need("--gpio-b"), nullptr, 0));
        else if (a == "--gpio-c") opt.gpio_c = uint16_t(std::stoul(need("--gpio-c"), nullptr, 0));
        else if (a == "--gpio-d") opt.gpio_d = uint16_t(std::stoul(need("--gpio-d"), nullptr, 0));
        else if (a == "--gpio-e") opt.gpio_e = uint16_t(std::stoul(need("--gpio-e"), nullptr, 0));
        else if (a == "--battery-adc") opt.battery_adc = uint16_t(
            std::stoul(need("--battery-adc"), nullptr, 0) & 0x0fff);
        else if (a == "--help" || a == "-h") {
            std::cout << "usage: mobigo2_emu ... [--nand path] [--mba path] "
                         "[--touch-event at,duration,x,y] "
                         "[--key-event at,duration,key] [--usb] [--audio] "
                         "[--render-interval N] [--max-present-hz N] "
                         "[--open-window-at N] [--start-logging-at N] [--log] "
                         "[--log-file path] ...\n";
            std::exit(0);
        } else {
            die("unknown argument: " + a);
        }
    }
    std::sort(opt.scripted_touches.begin(), opt.scripted_touches.end(),
              [](const ScriptedTouch &a, const ScriptedTouch &b) { return a.at < b.at; });
    for (size_t i = 1; i < opt.scripted_touches.size(); ++i) {
        const ScriptedTouch &previous = opt.scripted_touches[i - 1];
        if (opt.scripted_touches[i].at < previous.at + previous.duration)
            die("--touch-event ranges must not overlap");
    }
    std::stable_sort(
        opt.scripted_key_transitions.begin(), opt.scripted_key_transitions.end(),
        [](const ScriptedKeyTransition &a, const ScriptedKeyTransition &b) {
            if (a.at != b.at) return a.at < b.at;
            return a.pressed && !b.pressed;
        });
    return opt;
}

} // namespace mobigo
