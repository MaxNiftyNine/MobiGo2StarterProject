#include "video.hpp"

#include <iostream>
#include <stdexcept>

using namespace mobigo;

static void require(bool condition, const char *message) {
    if (!condition) throw std::runtime_error(message);
}

static void test_mba_entry_return_is_an_application_exit() {
    Bus bus;
    Cpu cpu(bus);
    constexpr uint32_t entry = 0x0e0100;
    bus.sdram[entry - kCsBase] = 0x9a90; // RETF: pop SR, PC from SP

    cpu.reset_core(0x020000);
    cpu.push(0x1234, cpu.r[Cpu::SP]);
    cpu.push(0x0002, cpu.r[Cpu::SP]);
    cpu.r[Cpu::SR] = uint16_t(entry >> 16);
    cpu.r[Cpu::PC] = uint16_t(entry);
    bus.configure_mba_watchdog_handoff(entry);

    cpu.step();

    require(bus.mba_launch_count == 1, "MBA entry was not recorded as an application launch");
    require(bus.mba_return_count == 1, "top-level MBA RETF was not recorded as an application exit");
    require(!bus.mba_application_active, "returned MBA remained marked active");
    require(cpu.lpc() == 0x021234, "MBA RETF did not return to its LD caller");
}

static void test_mba_scanout_requires_inherited_interrupt_service() {
    Bus bus;
    Cpu cpu(bus);
    Video video;
    constexpr uint32_t entry = 0x0e0100;
    constexpr uint32_t framebuffer = 0x3fd400;

    video.pixels.assign(Video::W * Video::H, 0xffffffffu);
    bus.mmio[0x7078 - kMmioBase] = uint16_t(framebuffer);
    bus.mmio[0x7079 - kMmioBase] = uint16_t(framebuffer >> 16);
    bus.mmio[0x707f - kMmioBase] = 0x0088;
    for (uint32_t i = 0; i < Video::W * Video::H; ++i)
        bus.dma_write(framebuffer + i, 0xf800);

    bus.configure_mba_watchdog_handoff(entry);
    bus.maybe_begin_mba_application(entry, 0x6ffd);
    bus.maybe_arm_mba_watchdog_handoff(entry, 0x6ffd);
    cpu.enable_irq = 0;
    cpu.enable_fiq = 0;
    video.compose(bus, cpu, false);
    require(video.pixels[0] == 0xffffffffu,
            "interrupt-disabled MBA exposed an unlatched framebuffer");

    cpu.enable_irq = 1;
    video.compose(bus, cpu, false);
    require(video.pixels[0] == Video::rgb565_to_argb(0xf800),
            "interrupt-serviced MBA did not latch its framebuffer");
}

static void test_ppu_bit_zero_is_not_a_global_enable() {
    Bus bus;
    Video video;
    bus.mmio[0x707f - kMmioBase] = 0x0000;
    bus.mmio[0x7042 - kMmioBase] = 0x0001;
    require(video.render_ppu(bus),
            "P_PPU_Enable bit zero incorrectly disabled the GPL16250VA PPU");
}

static void test_rtc_hms_counters_advance() {
    Bus bus;
    bus.cycles = 1;
    bus.write(0x7920, 59);
    bus.write(0x7921, 59);
    bus.write(0x7922, 23);
    bus.write(0x7934, 0x8000);
    bus.update_periodic_events();

    bus.cycles += bus.system_clock_hz();
    bus.update_periodic_events();

    require(bus.read(0x7920) == 0, "RTC second did not wrap at 60");
    require(bus.read(0x7921) == 0, "RTC minute did not wrap at 60");
    require(bus.read(0x7922) == 0, "RTC hour did not wrap at 24");
    require((bus.read(0x7935) & 0x000e) == 0x000e,
            "RTC second/minute/hour status flags were not latched");
}

static void test_official_fixed_source_dma_completion_path() {
    Bus bus;
    constexpr uint32_t source = 0x002000;
    constexpr uint32_t target = 0x002100;
    bus.write(source, 0x07e0);
    bus.write(0x7a81, uint16_t(source));
    bus.write(0x7a84, uint16_t(source >> 16));
    bus.write(0x7a82, uint16_t(target));
    bus.write(0x7a85, uint16_t(target >> 16));
    bus.write(0x7a83, 4);
    bus.write(0x7a86, 0);
    bus.write(0x7a80, 0x0089); // fixed source + normal completion + enable

    for (uint32_t i = 0; i < 4; ++i)
        require(bus.read(target + i) == 0x07e0, "fixed-source DMA fill produced bad data");
    require((bus.read(0x7abf) & 0x0001) != 0, "DMA completion flag was not set");
    require((bus.read(0x7a80) & 0x0003) == 0, "DMA enable/busy bits did not clear");
    bus.write(0x7abf, 0x0001);
    require((bus.read(0x7abf) & 0x0001) == 0, "DMA completion W1C failed");
}

static void test_dma_loaded_mba_header_registers_entry() {
    Bus bus;
    constexpr uint32_t source = 0x002400;
    constexpr uint32_t target = 0x0c8000;
    constexpr uint32_t entry = 0x0e1b60;
    bus.write(source + 0, 0x4d62);
    bus.write(source + 1, 0x675f);
    bus.write(source + 2, 0x4d62);
    bus.write(source + 3, 0x6151);
    bus.write(source + 0x0a, uint16_t(entry));
    bus.write(source + 0x0b, uint16_t(entry >> 16));
    bus.write(source + 0x0c, 0x1800);
    bus.write(source + 0x0d, 0x000e);
    bus.write(0x7a81, uint16_t(source));
    bus.write(0x7a84, uint16_t(source >> 16));
    bus.write(0x7a82, uint16_t(target));
    bus.write(0x7a85, uint16_t(target >> 16));
    bus.write(0x7a83, 0x10);
    bus.write(0x7a86, 0);
    bus.write(0x7a80, 0x0009);

    require(bus.mba_application_entry == entry,
            "DMA-loaded MBA header did not register its application entry");
    require(bus.mba_application_handoff_pending,
            "DMA-loaded MBA entry was not armed for lifecycle tracking");
    require(!bus.mba_watchdog_handoff_pending,
            "ordinary retail MBA incorrectly received replacement watchdog injection");
}

int main() {
    test_mba_entry_return_is_an_application_exit();
    test_mba_scanout_requires_inherited_interrupt_service();
    test_ppu_bit_zero_is_not_a_global_enable();
    test_rtc_hms_counters_advance();
    test_official_fixed_source_dma_completion_path();
    test_dma_loaded_mba_header_registers_entry();
    std::cout << "hardware accuracy tests passed\n";
    return 0;
}
